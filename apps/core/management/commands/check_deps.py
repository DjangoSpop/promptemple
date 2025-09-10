"""
Management command to check dependency compatibility
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Check dependency compatibility to prevent pydantic/langchain conflicts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Fail on any compatibility issues',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking dependency compatibility...'))
        
        issues = []
        warnings = []
        
        # Check Pydantic version
        try:
            import pydantic
            pydantic_version = pydantic.__version__
            pydantic_major = int(pydantic_version.split('.')[0])
            
            self.stdout.write(f'Pydantic version: {pydantic_version}')
            
            if pydantic_major < 2:
                warnings.append(f'Pydantic v{pydantic_version} is old. Consider upgrading to v2 for better performance.')
            
        except ImportError:
            issues.append('Pydantic not installed')
        
        # Check LangChain version
        try:
            import langchain
            langchain_version = langchain.__version__
            langchain_parts = langchain_version.split('.')
            langchain_major = int(langchain_parts[0])
            langchain_minor = int(langchain_parts[1]) if len(langchain_parts) > 1 else 0
            
            self.stdout.write(f'LangChain version: {langchain_version}')
            
            # Check for incompatible combinations
            if pydantic_major >= 2 and (langchain_major == 0 and langchain_minor < 2):
                issues.append(
                    f'Incompatible: Pydantic v{pydantic_version} with LangChain v{langchain_version}. '
                    'Use LangChain ≥ 0.2 with Pydantic v2.'
                )
            
            if langchain_major == 0 and langchain_minor < 2:
                warnings.append(f'LangChain v{langchain_version} is old. Consider upgrading to ≥ 0.2.')
            
        except ImportError:
            self.stdout.write('LangChain not installed (optional)')
        
        # Check Django version
        try:
            import django
            django_version = django.__version__
            self.stdout.write(f'Django version: {django_version}')
        except ImportError:
            issues.append('Django not installed (should not happen)')
        
        # Check RAG service status
        try:
            from apps.templates.rag.services import langchain_status
            rag_status = langchain_status()
            
            if rag_status['feature_enabled']:
                if rag_status['service_ready']:
                    self.stdout.write(self.style.SUCCESS('✓ RAG service ready'))
                else:
                    warning_msg = f"RAG service enabled but not ready: {rag_status.get('error', 'Unknown error')}"
                    warnings.append(warning_msg)
            else:
                self.stdout.write('RAG service disabled (FEATURE_RAG=0)')
                
        except Exception as e:
            warnings.append(f'Could not check RAG service: {e}')
        
        # Report results
        if issues:
            self.stdout.write(self.style.ERROR('\nCompatibility Issues:'))
            for issue in issues:
                self.stdout.write(self.style.ERROR(f'✗ {issue}'))
        
        if warnings:
            self.stdout.write(self.style.WARNING('\nWarnings:'))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'⚠ {warning}'))
        
        if not issues and not warnings:
            self.stdout.write(self.style.SUCCESS('\n✓ All dependency checks passed'))
        elif not issues:
            self.stdout.write(self.style.SUCCESS(f'\n✓ No critical issues found ({len(warnings)} warnings)'))
        
        # Exit with error code if strict mode and there are issues
        if options['strict'] and issues:
            self.stdout.write(self.style.ERROR('\nFailing due to --strict mode'))
            sys.exit(1)
        
        self.stdout.write('\nRecommendations:')
        self.stdout.write('- Use constraints.txt when installing: pip install -r requirements.txt -c constraints.txt')
        self.stdout.write('- Set FEATURE_RAG=0 if experiencing LangChain issues')
        self.stdout.write('- Run this check after any dependency changes')