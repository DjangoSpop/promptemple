# 🚀 Template Ingestion - Quick Start Guide

## Installation & Usage

### Command Syntax
```bash
python manage.py ingest_100k_prompts <file_path> [options]
```

### Supported Formats
- **JSONL** (recommended): `prompt_dataset_v1.jsonl` - one JSON object per line
- **JSON**: Array of objects or single object
- **CSV**: With headers matching field names

### Basic Examples

#### 1. Simple Ingestion
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl
```
✅ Auto-detects format from `.jsonl` extension
✅ Uses default settings (batch=1000, workers=4)
✅ Skips duplicates automatically

#### 2. High-Quality Templates Only
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --min-quality=75
```
⚠️ Filters templates with quality_score < 75

#### 3. Fast Processing (Many Workers)
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --workers=16 --batch-size=2000
```
⚡ 16 parallel threads, 2K batch size
💡 For 100K+ records on powerful hardware

#### 4. Test with Sample
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --sample-size=100
```
🧪 Process only first 100 records

#### 5. Validation Without Saving
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --dry-run
```
✓ Validates data structure without database changes

#### 6. Fresh Start (Clear & Re-ingest)
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --clear-existing
```
🗑️ Deletes all existing templates first

---

## 📊 Expected Output

```
🚀 Starting 100K+ Template Ingestion Process...
📋 Auto-detected format: jsonl
✅ File validated: prompt_dataset_v1.jsonl (45.3MB)
📂 Loading data from prompt_dataset_v1.jsonl...
✅ Loaded 50,000 records in 3.45s
⚠️  Filtered out 125 low-quality templates (quality < 60)
⚙️  Processing 49,875 templates in batches of 1000...
📦 Created 50 batches
📊 Progress: 12,500/49,875 (25.0%) | Errors: 23
...
✅ INGESTION COMPLETED SUCCESSFULLY
📊 Total templates processed: 49,852
⚠️  Errors encountered: 23
✅ Success rate: 99.95%
⏱️  Average time per template: 0.82ms
⚡ Processing rate: 1,220.3 templates/second
⏳ Total processing time: 40.84s (0.7m)
💾 Total templates in database: 127,450
🚀 Ready for search and optimization!
```

---

## 🔍 Real-Time Monitoring

While ingestion runs, you can:

```bash
# In another terminal, monitor database growth
watch 'python manage.py shell -c "from apps.templates.models import Template; print(f\"Templates: {Template.objects.count()}\")"'

# Or check logs
tail -f logs/django.log
```

---

## ✅ Verification

After ingestion completes:

```python
# Django shell
python manage.py shell

from apps.templates.models import Template, TemplateCategory

# Check totals
print(f"Templates: {Template.objects.count()}")
print(f"Categories: {TemplateCategory.objects.count()}")

# View sample
template = Template.objects.first()
print(f"Title: {template.title}")
print(f"Quality: {template.ai_confidence * 100:.1f}%")
print(f"Tags: {template.tags}")
print(f"Fields: {template.fields.count()}")
```

---

## 🛠️ Troubleshooting

### Issue: "File not found"
**Solution:** Provide absolute path or check file location
```bash
# Absolute path
python manage.py ingest_100k_prompts /full/path/to/prompt_dataset_v1.jsonl

# Relative path from project root
python manage.py ingest_100k_prompts ./data/prompt_dataset_v1.jsonl
```

### Issue: "Redis not available" warning
**Solution:** This is OK! In-memory cache will be used
```
⚠️ Redis not available, using in-memory cache
```
✅ No impact on ingestion performance
💡 For production, configure Redis connection

### Issue: "Low success rate"
**Check:** Data quality and format
```bash
# Validate with dry-run first
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --dry-run

# Check first few records
head -5 prompt_dataset_v1.jsonl | jq .

# Test with small sample
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --sample-size=10
```

### Issue: "Memory usage high"
**Solution:** Reduce batch size and worker threads
```bash
python manage.py ingest_100k_prompts prompt_dataset_v1.jsonl --batch-size=500 --workers=2
```

---

## 📈 Performance Tips

| Scenario | Command |
|----------|---------|
| **Slow server** | `--batch-size=500 --workers=2` |
| **Fast server** | `--batch-size=5000 --workers=16` |
| **Limited RAM** | `--batch-size=250 --workers=1` |
| **Testing** | `--sample-size=100 --dry-run` |
| **High quality only** | `--min-quality=80` |

---

## 🔗 Related Components

### SSE Validation Endpoint
```
GET /api/templates/{template_id}/validate/stream/
```
Returns real-time quality assessment with streaming progress

### Admin Interface
```
http://localhost:8000/admin/templates/template/
```
View & manage ingested templates

### Data Sources
- `prompt_dataset_v1.jsonl` - Main dataset
- `prompt_dataset_v1.csv` - Alternative format
- `prompt_dataset_v1.json` - Single file array

---

## 📋 Required Fields (Minimum)

For each template record, you need:
- `prompt_title` ✅
- `prompt_template` ✅
- `description` ✅

Optional but recommended:
- `intent_category`
- `domain`
- `required_inputs`
- `optional_inputs`
- `ideal_models`
- `power_tips`
- `metadata.quality_score`
- `metadata.complexity`
- `metadata.framework`

---

## 💾 Database Impact

**Before:** 
- 0 templates, 0 categories

**After (typical 100K ingestion):**
- ~47,000-50,000 templates
- ~15-20 categories
- ~200,000-250,000 field records
- Database size: ~300-500MB (depending on content)

---

## 📞 Support

For issues or questions:
1. Check **INGESTION_IMPLEMENTATION.md** for details
2. Review Django logs: `logs/django.log`
3. Test with `--dry-run` first
4. Check data format matches examples above

---

**Version:** 1.0.0
**Last Updated:** November 15, 2025
**Status:** ✅ Production Ready
