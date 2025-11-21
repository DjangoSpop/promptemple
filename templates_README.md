# Template System Documentation

This document explains how to work with the PromptCraft template system, including loading templates into the database and accessing them through the API.

## Overview

The template system allows you to create, manage, and access AI prompt templates through a RESTful API. Templates are stored in the database and can be loaded from JSON files.

## Template Structure

Each template includes:

- Basic information (title, description, etc.)
- Template content with placeholders
- Form fields for user input
- Metadata and organization (categories, tags)

## Loading Templates

There are several ways to load templates into the database:

### 1. Using the Management Command

The most efficient way to load templates is using the Django management command:

```bash
python manage.py updatetemplates
```

Options:
- `--force`: Update existing templates instead of skipping them

### 2. Using the Template DB Tool

For more comprehensive template management:

```bash
python template_db_tool.py populate
```

This script provides additional options and verification.

### 3. Using the PowerShell Script

On Windows, you can use the PowerShell script:

```powershell
./setup_templates.ps1
```

## Template JSON Files

Templates are defined in JSON files:

- `creative_templates.json`: Creative writing templates
- `software_templates.json`: Software development templates
- `advanced_storytelling_templates.json`: Advanced storytelling templates
- `star_interview.json`: STAR interview template

## API Endpoints

Once loaded, templates are accessible through these API endpoints:

- `GET /api/templates/`: List all templates
- `GET /api/template-categories/`: List all template categories
- `GET /api/templates/{id}/`: Get a specific template
- `GET /api/templates/trending/`: Get trending templates
- `GET /api/templates/featured/`: Get featured templates
- `GET /api/template-categories/{id}/templates/`: Get templates in a category

## Testing the API

To test if templates are accessible through the API:

```bash
python test_api_endpoints.py
```

## Checking the Database

To check if templates are properly stored in the database:

```bash
python check_db.py
```

## Creating Custom Templates

To create new templates:

1. Create a JSON file following the format in existing template files
2. Add the file path to the `JSON_FILES` list in `populate_templates.py` or `updatetemplates.py`
3. Run the appropriate command to load the templates

## Troubleshooting

If you encounter issues:

1. Check if the database connection is working with `python check_db.py`
2. Make sure all required dependencies are installed with `./fix_requirements.ps1`
3. Verify that migrations have been applied with `python manage.py migrate`
4. Check for errors in the JSON files

## Database Models

The template system uses these main models:

- `TemplateCategory`: Categories for organizing templates
- `Template`: The main template model
- `PromptField`: Individual fields for template forms
- `TemplateField`: Association between templates and fields

For more information, see the models defined in `apps/templates/models.py`.
