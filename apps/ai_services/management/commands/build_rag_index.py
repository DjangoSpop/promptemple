"""
Management command to build/rebuild RAG index for prompt optimization
"""

import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.ai_services.rag_service_enhanced import get_document_indexer


class Command(BaseCommand):
    help = 'Build or rebuild the RAG (Retrieval-Augmented Generation) index for prompt optimization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force rebuild even if index is recent',
        )
        
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress information',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        
        self.stdout.write('🔧 Building RAG Index for Prompt Optimization')
        self.stdout.write('=' * 50)
        
        try:
            # Get the document indexer
            indexer = get_document_indexer()
            
            if options['verbose']:
                self.stdout.write(f"📁 Index path: {indexer.index_path}")
                self.stdout.write(f"📊 Chunk size: {indexer.chunk_size}")
                self.stdout.write(f"🔄 Chunk overlap: {indexer.chunk_overlap}")
                
            # Load documents first to check
            self.stdout.write("📚 Loading documents...")
            documents = indexer.load_documents()
            
            if not documents:
                raise CommandError("❌ No documents found to index")
            
            self.stdout.write(f"✅ Found {len(documents)} documents")
            
            if options['verbose']:
                # Show document breakdown
                doc_types = {}
                for doc in documents:
                    doc_type = doc.metadata.get('type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                self.stdout.write("📋 Document breakdown:")
                for doc_type, count in doc_types.items():
                    self.stdout.write(f"   - {doc_type}: {count}")
            
            # Build the index
            self.stdout.write("🔨 Building vector index...")
            
            if options['force']:
                self.stdout.write("⚠️  Force rebuild enabled")
            
            success = indexer.build_index(force_rebuild=options['force'])
            
            if success:
                elapsed = time.time() - start_time
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ RAG index built successfully in {elapsed:.1f} seconds"
                    )
                )
                
                # Show index stats
                metadata_file = indexer.index_path / "metadata.json"
                if metadata_file.exists():
                    import json
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    self.stdout.write("📊 Index Statistics:")
                    self.stdout.write(f"   - Documents: {metadata.get('document_count', 'N/A')}")
                    self.stdout.write(f"   - Chunks: {metadata.get('chunk_count', 'N/A')}")
                    self.stdout.write(f"   - Last built: {metadata.get('last_build', 'N/A')}")
                
                self.stdout.write("\n🚀 RAG system is ready for prompt optimization!")
                
            else:
                raise CommandError("❌ Failed to build index")
                
        except Exception as e:
            raise CommandError(f"❌ Index building failed: {e}")