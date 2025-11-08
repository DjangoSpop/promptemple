"""
Management command to generate API coverage reports from OpenAPI spec
"""
import csv
import json
import yaml
from pathlib import Path
from collections import defaultdict
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate API coverage report from OpenAPI specification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--spec',
            type=str,
            default='PromptCraft API.yaml',
            help='Path to OpenAPI spec file (YAML or JSON)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='var/reports',
            help='Output directory for reports'
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['all', 'markdown', 'csv', 'json'],
            default='all',
            help='Output format'
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        spec_path = base_dir / options['spec']
        output_dir = base_dir / options['output_dir']
        output_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.SUCCESS(f'📊 Analyzing API coverage from: {spec_path}'))

        if not spec_path.exists():
            raise CommandError(f'Spec file not found: {spec_path}')

        # Load OpenAPI spec
        try:
            with open(spec_path, 'r', encoding='utf-8') as f:
                if spec_path.suffix in ['.yaml', '.yml']:
                    spec = yaml.safe_load(f)
                else:
                    spec = json.load(f)
        except Exception as e:
            raise CommandError(f'Failed to parse spec: {e}')

        # Analyze spec
        analysis = self.analyze_spec(spec)

        # Generate reports
        fmt = options['format']
        if fmt in ['all', 'markdown']:
            self.generate_markdown(analysis, output_dir / 'api_coverage.md')
        if fmt in ['all', 'csv']:
            self.generate_csv(analysis, output_dir / 'api_coverage.csv')
        if fmt in ['all', 'json']:
            self.generate_json(analysis, output_dir / 'api_coverage.json')

        # Print summary
        self.print_summary(analysis)

    def analyze_spec(self, spec):
        """Analyze OpenAPI spec and extract coverage data"""
        info = spec.get('info', {})
        paths = spec.get('paths', {})
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        security_schemes = components.get('securitySchemes', {})

        endpoints = []
        method_counts = defaultdict(int)
        auth_types = set()
        status_codes = set()
        gaps = []

        for path, path_item in paths.items():
            for method in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                if method not in path_item:
                    continue

                operation = path_item[method]
                operation_id = operation.get('operationId', 'N/A')
                description = operation.get('description', operation.get('summary', ''))
                parameters = operation.get('parameters', [])
                request_body = operation.get('requestBody', {})
                responses = operation.get('responses', {})
                security = operation.get('security', [])
                tags = operation.get('tags', [])

                # Extract request schema
                request_schema = None
                if request_body:
                    content = request_body.get('content', {})
                    json_content = content.get('application/json', {})
                    request_schema = json_content.get('schema', {}).get('$ref', 'N/A')
                    if request_schema and request_schema.startswith('#/components/schemas/'):
                        request_schema = request_schema.split('/')[-1]

                # Extract response schemas
                response_schemas = {}
                for status, response in responses.items():
                    content = response.get('content', {})
                    json_content = content.get('application/json', {})
                    schema_ref = json_content.get('schema', {}).get('$ref', '')
                    if schema_ref and schema_ref.startswith('#/components/schemas/'):
                        response_schemas[status] = schema_ref.split('/')[-1]
                    elif 'description' in response:
                        response_schemas[status] = response['description']
                    status_codes.add(status)

                # Determine auth requirements
                auth_required = 'Yes' if security else 'Optional'
                if security:
                    for sec_item in security:
                        auth_types.update(sec_item.keys())

                # Query parameters
                query_params = [p['name'] for p in parameters if p.get('in') == 'query']
                pagination = any(p in ['page', 'page_size', 'limit', 'offset'] for p in query_params)

                # Check for gaps
                endpoint_gaps = []
                if not operation_id or operation_id == 'N/A':
                    endpoint_gaps.append('Missing operationId')
                if not description:
                    endpoint_gaps.append('Missing description')
                if not responses:
                    endpoint_gaps.append('No responses documented')
                if request_body and not request_schema:
                    endpoint_gaps.append('Request body lacks schema reference')

                if endpoint_gaps:
                    gaps.append({
                        'endpoint': f'{method.upper()} {path}',
                        'issues': endpoint_gaps
                    })

                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'operation_id': operation_id,
                    'description': description[:100] + '...' if len(description) > 100 else description,
                    'tags': ', '.join(tags),
                    'auth': auth_required,
                    'request_schema': request_schema or 'N/A',
                    'response_schemas': response_schemas,
                    'status_codes': ', '.join(responses.keys()),
                    'pagination': 'Yes' if pagination else 'No',
                    'query_params': ', '.join(query_params[:5]),
                    'has_gaps': bool(endpoint_gaps),
                })

                method_counts[method.upper()] += 1

        # Calculate coverage metrics
        total_endpoints = len(endpoints)
        endpoints_with_schemas = sum(1 for e in endpoints if e['request_schema'] != 'N/A' or e['response_schemas'])
        endpoints_with_docs = sum(1 for e in endpoints if e['description'] and e['description'] != 'N/A')
        endpoints_with_gaps = sum(1 for e in endpoints if e['has_gaps'])

        coverage = {
            'api_info': {
                'title': info.get('title', 'N/A'),
                'version': info.get('version', 'N/A'),
                'description': info.get('description', 'N/A'),
            },
            'metrics': {
                'total_endpoints': total_endpoints,
                'total_paths': len(paths),
                'total_schemas': len(schemas),
                'method_breakdown': dict(method_counts),
                'endpoints_with_schemas': endpoints_with_schemas,
                'endpoints_with_docs': endpoints_with_docs,
                'endpoints_with_gaps': endpoints_with_gaps,
                'coverage_percentage': round((endpoints_with_docs / total_endpoints * 100) if total_endpoints > 0 else 0, 2),
                'schema_coverage': round((endpoints_with_schemas / total_endpoints * 100) if total_endpoints > 0 else 0, 2),
            },
            'auth_types': list(auth_types) if auth_types else ['None'],
            'status_codes': sorted(status_codes),
            'endpoints': endpoints,
            'gaps': gaps,
            'schemas': list(schemas.keys()),
        }

        return coverage

    def generate_markdown(self, analysis, output_path):
        """Generate Markdown coverage report"""
        metrics = analysis['metrics']
        info = analysis['api_info']

        md_lines = [
            f"# API Coverage Report: {info['title']}",
            f"",
            f"**Version:** {info['version']}  ",
            f"**Generated:** {Path(__file__).stat().st_mtime}  ",
            f"**Description:** {info['description']}",
            f"",
            f"## 📊 Coverage Metrics",
            f"",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Endpoints | {metrics['total_endpoints']} |",
            f"| Total Paths | {metrics['total_paths']} |",
            f"| Total Schemas | {metrics['total_schemas']} |",
            f"| Endpoints with Documentation | {metrics['endpoints_with_docs']} ({metrics['coverage_percentage']}%) |",
            f"| Endpoints with Schemas | {metrics['endpoints_with_schemas']} ({metrics['schema_coverage']}%) |",
            f"| Endpoints with Gaps | {metrics['endpoints_with_gaps']} |",
            f"",
            f"### Methods Breakdown",
            f"",
        ]

        for method, count in sorted(analysis['metrics']['method_breakdown'].items()):
            md_lines.append(f"- **{method}**: {count} endpoints")

        md_lines.extend([
            f"",
            f"### Authentication Types",
            f"",
        ])

        for auth in analysis['auth_types']:
            md_lines.append(f"- {auth}")

        md_lines.extend([
            f"",
            f"### Status Codes",
            f"",
            f"{', '.join(analysis['status_codes'])}",
            f"",
            f"## 📋 Endpoint Details",
            f"",
            f"| Method | Path | Operation ID | Auth | Request Schema | Status Codes | Pagination | Gaps |",
            f"|--------|------|--------------|------|----------------|--------------|------------|------|",
        ])

        for ep in analysis['endpoints']:
            gaps_icon = '⚠️' if ep['has_gaps'] else '✅'
            md_lines.append(
                f"| {ep['method']} | `{ep['path']}` | `{ep['operation_id']}` | {ep['auth']} | "
                f"`{ep['request_schema']}` | {ep['status_codes']} | {ep['pagination']} | {gaps_icon} |"
            )

        if analysis['gaps']:
            md_lines.extend([
                f"",
                f"## ⚠️ Gaps & Issues",
                f"",
            ])

            for gap in analysis['gaps']:
                md_lines.append(f"### {gap['endpoint']}")
                for issue in gap['issues']:
                    md_lines.append(f"- {issue}")
                md_lines.append("")

        md_lines.extend([
            f"",
            f"## 📦 Available Schemas",
            f"",
        ])

        for schema in sorted(analysis['schemas'][:50]):  # Limit to first 50
            md_lines.append(f"- `{schema}`")

        if len(analysis['schemas']) > 50:
            md_lines.append(f"- ... and {len(analysis['schemas']) - 50} more")

        md_lines.extend([
            f"",
            f"## ✅ Next Steps",
            f"",
            f"1. Address gaps identified above",
            f"2. Implement UI pages for all endpoints",
            f"3. Generate contract tests for each operation",
            f"4. Add pagination tests where applicable",
            f"5. Test authentication flows",
            f"6. Validate all request/response schemas",
            f"",
        ])

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md_lines))

        self.stdout.write(self.style.SUCCESS(f'✅ Markdown report saved to: {output_path}'))

    def generate_csv(self, analysis, output_path):
        """Generate CSV coverage report"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'Method', 'Path', 'Operation ID', 'Tags', 'Auth', 'Request Schema',
                'Response Schemas', 'Status Codes', 'Pagination', 'Query Params', 
                'Has Gaps', 'Description'
            ])
            writer.writeheader()

            for ep in analysis['endpoints']:
                writer.writerow({
                    'Method': ep['method'],
                    'Path': ep['path'],
                    'Operation ID': ep['operation_id'],
                    'Tags': ep['tags'],
                    'Auth': ep['auth'],
                    'Request Schema': ep['request_schema'],
                    'Response Schemas': json.dumps(ep['response_schemas']),
                    'Status Codes': ep['status_codes'],
                    'Pagination': ep['pagination'],
                    'Query Params': ep['query_params'],
                    'Has Gaps': ep['has_gaps'],
                    'Description': ep['description'],
                })

        self.stdout.write(self.style.SUCCESS(f'✅ CSV report saved to: {output_path}'))

    def generate_json(self, analysis, output_path):
        """Generate JSON coverage report"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f'✅ JSON report saved to: {output_path}'))

    def print_summary(self, analysis):
        """Print coverage summary to console"""
        metrics = analysis['metrics']

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('📊 API COVERAGE SUMMARY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"Total Endpoints: {metrics['total_endpoints']}")
        self.stdout.write(f"Documentation Coverage: {metrics['coverage_percentage']}%")
        self.stdout.write(f"Schema Coverage: {metrics['schema_coverage']}%")
        self.stdout.write(f"Endpoints with Gaps: {metrics['endpoints_with_gaps']}")
        
        if metrics['endpoints_with_gaps'] > 0:
            self.stdout.write(self.style.WARNING(f"\n⚠️  {metrics['endpoints_with_gaps']} endpoints need attention"))
        else:
            self.stdout.write(self.style.SUCCESS("\n✅ All endpoints fully documented!"))

        self.stdout.write(self.style.SUCCESS('=' * 60))
