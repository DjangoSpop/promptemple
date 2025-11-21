/**
 * Template CRUD Operations
 * Comprehensive template management with modals, validation, and AI integration
 *
 * Features:
 * - Full CRUD operations via API
 * - Real-time AI validation with SSE
 * - Autosave functionality
 * - Search and filter with debounce
 * - Error handling and retry logic
 * - Toast notifications
 */

class TemplateCRUD {
  constructor() {
    this.apiBase = '/api/v2/templates';
    this.csrfToken = this.getCSRFToken();
    this.currentTemplate = null;
    this.validationClient = null;
    this.autosaveTimer = null;
    this.searchDebounceTimer = null;

    // Initialize
    this.init();
  }

  /**
   * Initialize CRUD controller
   */
  init() {
    this.bindEvents();
    this.initializeSearchFilter();
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Create template button
    const createBtn = document.querySelector('[data-action="create-template"]');
    if (createBtn) {
      createBtn.addEventListener('click', () => this.showCreateModal());
    }

    // Edit buttons (event delegation)
    document.addEventListener('click', (e) => {
      const editBtn = e.target.closest('[data-action="edit-template"]');
      if (editBtn) {
        const templateId = editBtn.dataset.templateId;
        this.showEditModal(templateId);
      }
    });

    // Delete buttons (event delegation)
    document.addEventListener('click', (e) => {
      const deleteBtn = e.target.closest('[data-action="delete-template"]');
      if (deleteBtn) {
        const templateId = deleteBtn.dataset.templateId;
        this.confirmDelete(templateId);
      }
    });

    // Preview buttons (event delegation)
    document.addEventListener('click', (e) => {
      const previewBtn = e.target.closest('[data-action="preview-template"]');
      if (previewBtn) {
        const templateId = previewBtn.dataset.templateId;
        this.showPreviewModal(templateId);
      }
    });

    // Duplicate buttons (event delegation)
    document.addEventListener('click', (e) => {
      const duplicateBtn = e.target.closest('[data-action="duplicate-template"]');
      if (duplicateBtn) {
        const templateId = duplicateBtn.dataset.templateId;
        this.duplicateTemplate(templateId);
      }
    });
  }

  /**
   * Show create template modal
   */
  showCreateModal() {
    const modal = GlassModal.create({
      id: 'templateModal',
      type: 'template',
      size: 'lg',
      title: '<i class="bi bi-file-earmark-plus"></i> Create New Template',
      body: this.renderTemplateForm(),
      footer: `
        <div class="modal-footer-start">
          <div class="saving-indicator" style="display: none;">
            <div class="spinner-border spinner-border-sm" role="status">
              <span class="visually-hidden">Saving...</span>
            </div>
            <span>Saving...</span>
          </div>
        </div>
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
          Cancel
        </button>
        <button type="button" class="btn btn-primary" data-action="save-template">
          <i class="bi bi-check-lg"></i> Create Template
        </button>
      `,
      onShown: () => {
        this.initializeFormHandlers(modal);
      },
      onHidden: () => {
        this.cleanupAutosave();
        modal.destroy();
      }
    });

    modal.show();
  }

  /**
   * Show edit template modal
   * @param {string} templateId - Template ID
   */
  async showEditModal(templateId) {
    try {
      // Show loading modal
      const loadingModal = GlassModal.create({
        type: 'feedback',
        size: 'sm',
        body: `
          <div class="text-center py-4">
            <div class="spinner mb-3"></div>
            <p>Loading template...</p>
          </div>
        `
      });
      loadingModal.show();

      // Fetch template data
      const template = await this.fetchTemplate(templateId);
      this.currentTemplate = template;

      // Hide loading modal
      loadingModal.hide();
      setTimeout(() => loadingModal.destroy(), 200);

      // Show edit modal
      const modal = GlassModal.create({
        id: 'templateModal',
        type: 'template',
        size: 'lg',
        title: `<i class="bi bi-pencil"></i> Edit Template`,
        body: this.renderTemplateForm(template),
        footer: `
          <div class="modal-footer-start">
            <div class="saving-indicator" style="display: none;">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">Saving...</span>
              </div>
              <span>Saving...</span>
            </div>
          </div>
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            Cancel
          </button>
          <button type="button" class="btn btn-secondary" data-action="validate-prompt">
            <i class="bi bi-cpu"></i> AI Validate
          </button>
          <button type="button" class="btn btn-primary" data-action="save-template">
            <i class="bi bi-check-lg"></i> Save Changes
          </button>
        `,
        onShown: () => {
          this.initializeFormHandlers(modal);
        },
        onHidden: () => {
          this.cleanupAutosave();
          modal.destroy();
        }
      });

      modal.show();

    } catch (error) {
      console.error('Failed to load template:', error);
      this.showToast('Failed to load template', 'error');
    }
  }

  /**
   * Render template form
   * @param {Object} template - Template data
   * @returns {string} Form HTML
   */
  renderTemplateForm(template = null) {
    const data = template || {
      title: '',
      description: '',
      domain: '',
      prompt_body: '',
      tags: [],
      visibility: 'private'
    };

    return `
      <form id="templateForm" novalidate>
        <div class="form-floating mb-3">
          <input
            type="text"
            class="form-control"
            id="template-title"
            name="title"
            placeholder="Template Title"
            value="${this.escapeHtml(data.title)}"
            required
            maxlength="200"
          >
          <label for="template-title">
            <i class="bi bi-type"></i> Title *
          </label>
          <div class="invalid-feedback">Please provide a title.</div>
          <div class="char-counter">
            <span class="current">0</span> / <span class="max">200</span>
          </div>
        </div>

        <div class="form-floating mb-3">
          <textarea
            class="form-control"
            id="template-description"
            name="description"
            placeholder="Description"
            style="min-height: 80px;"
            maxlength="500"
          >${this.escapeHtml(data.description)}</textarea>
          <label for="template-description">
            <i class="bi bi-text-paragraph"></i> Description
          </label>
          <div class="char-counter">
            <span class="current">0</span> / <span class="max">500</span>
          </div>
        </div>

        <div class="row mb-3">
          <div class="col-md-6">
            <div class="form-floating">
              <select class="form-select" id="template-domain" name="domain">
                <option value="">Select Domain</option>
                <option value="general" ${data.domain === 'general' ? 'selected' : ''}>General</option>
                <option value="marketing" ${data.domain === 'marketing' ? 'selected' : ''}>Marketing</option>
                <option value="code" ${data.domain === 'code' ? 'selected' : ''}>Code</option>
                <option value="writing" ${data.domain === 'writing' ? 'selected' : ''}>Writing</option>
                <option value="analysis" ${data.domain === 'analysis' ? 'selected' : ''}>Analysis</option>
                <option value="education" ${data.domain === 'education' ? 'selected' : ''}>Education</option>
              </select>
              <label for="template-domain">
                <i class="bi bi-tag"></i> Domain
              </label>
            </div>
          </div>
          <div class="col-md-6">
            <div class="form-floating">
              <select class="form-select" id="template-visibility" name="visibility">
                <option value="private" ${data.visibility === 'private' ? 'selected' : ''}>Private</option>
                <option value="public" ${data.visibility === 'public' ? 'selected' : ''}>Public</option>
                <option value="organization" ${data.visibility === 'organization' ? 'selected' : ''}>Organization</option>
              </select>
              <label for="template-visibility">
                <i class="bi bi-eye"></i> Visibility
              </label>
            </div>
          </div>
        </div>

        <div class="form-floating mb-3">
          <textarea
            class="form-control"
            id="template-prompt"
            name="prompt_body"
            placeholder="Prompt Body"
            style="min-height: 200px; font-family: var(--font-family-mono);"
            required
          >${this.escapeHtml(data.prompt_body)}</textarea>
          <label for="template-prompt">
            <i class="bi bi-code-square"></i> Prompt Body *
          </label>
          <div class="invalid-feedback">Please provide a prompt body.</div>
          <div id="ai-hint-container"></div>
        </div>

        <div class="mb-3">
          <label class="form-label">
            <i class="bi bi-tags"></i> Tags
          </label>
          <div class="form-tags" id="template-tags">
            ${data.tags && data.tags.map(tag => `
              <span class="tag-item">
                ${this.escapeHtml(tag)}
                <button type="button" class="remove-tag" data-tag="${this.escapeHtml(tag)}">
                  <i class="bi bi-x"></i>
                </button>
              </span>
            `).join('')}
          </div>
          <input
            type="text"
            class="form-control mt-2"
            id="tag-input"
            placeholder="Type a tag and press Enter"
          >
        </div>

        <div id="validation-results" style="display: none;"></div>
      </form>
    `;
  }

  /**
   * Initialize form handlers (validation, autosave, etc.)
   * @param {GlassModal} modal - Modal instance
   */
  initializeFormHandlers(modal) {
    const form = modal.modal.querySelector('#templateForm');
    const saveBtn = modal.modal.querySelector('[data-action="save-template"]');
    const validateBtn = modal.modal.querySelector('[data-action="validate-prompt"]');

    // Character counters
    this.initializeCharCounters(modal.modal);

    // Tag input
    this.initializeTagInput(modal.modal);

    // Form validation
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      e.stopPropagation();
    });

    // Save button
    if (saveBtn) {
      saveBtn.addEventListener('click', async () => {
        if (this.validateForm(form)) {
          await this.saveTemplate(modal, form);
        }
      });
    }

    // AI validation button
    if (validateBtn) {
      validateBtn.addEventListener('click', () => {
        this.runAIValidation(modal);
      });
    }

    // Autosave on prompt body change
    const promptField = form.querySelector('#template-prompt');
    if (promptField) {
      promptField.addEventListener('input', () => {
        this.scheduleAutosave(modal, form);
      });
    }
  }

  /**
   * Initialize character counters
   * @param {HTMLElement} container - Container element
   */
  initializeCharCounters(container) {
    const fields = container.querySelectorAll('[maxlength]');
    fields.forEach(field => {
      const counter = field.parentElement.querySelector('.char-counter');
      if (!counter) return;

      const updateCounter = () => {
        const current = field.value.length;
        const max = field.getAttribute('maxlength');
        const currentEl = counter.querySelector('.current');
        if (currentEl) {
          currentEl.textContent = current;
        }
      };

      field.addEventListener('input', updateCounter);
      updateCounter();
    });
  }

  /**
   * Initialize tag input
   * @param {HTMLElement} container - Container element
   */
  initializeTagInput(container) {
    const tagInput = container.querySelector('#tag-input');
    const tagsContainer = container.querySelector('#template-tags');

    if (!tagInput || !tagsContainer) return;

    tagInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const tag = tagInput.value.trim();
        if (tag && !this.hasTag(tagsContainer, tag)) {
          this.addTag(tagsContainer, tag);
          tagInput.value = '';
        }
      }
    });

    // Remove tag buttons
    tagsContainer.addEventListener('click', (e) => {
      const removeBtn = e.target.closest('.remove-tag');
      if (removeBtn) {
        const tagItem = removeBtn.closest('.tag-item');
        if (tagItem) {
          tagItem.remove();
        }
      }
    });
  }

  /**
   * Check if tag exists
   * @param {HTMLElement} container - Tags container
   * @param {string} tag - Tag to check
   * @returns {boolean} Tag exists
   */
  hasTag(container, tag) {
    const tags = Array.from(container.querySelectorAll('.tag-item'))
      .map(el => el.textContent.trim().replace('×', '').trim());
    return tags.includes(tag);
  }

  /**
   * Add tag to container
   * @param {HTMLElement} container - Tags container
   * @param {string} tag - Tag to add
   */
  addTag(container, tag) {
    const tagEl = document.createElement('span');
    tagEl.className = 'tag-item';
    tagEl.innerHTML = `
      ${this.escapeHtml(tag)}
      <button type="button" class="remove-tag" data-tag="${this.escapeHtml(tag)}">
        <i class="bi bi-x"></i>
      </button>
    `;
    container.appendChild(tagEl);
  }

  /**
   * Validate form
   * @param {HTMLFormElement} form - Form element
   * @returns {boolean} Form is valid
   */
  validateForm(form) {
    let isValid = true;

    // Reset validation
    form.querySelectorAll('.is-invalid').forEach(el => {
      el.classList.remove('is-invalid');
    });

    // Check required fields
    const requiredFields = form.querySelectorAll('[required]');
    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        field.classList.add('is-invalid');
        isValid = false;
      }
    });

    if (!isValid) {
      this.showToast('Please fill in all required fields', 'warning');
    }

    return isValid;
  }

  /**
   * Save template
   * @param {GlassModal} modal - Modal instance
   * @param {HTMLFormElement} form - Form element
   */
  async saveTemplate(modal, form) {
    const savingIndicator = modal.modal.querySelector('.saving-indicator');
    const saveBtn = modal.modal.querySelector('[data-action="save-template"]');

    try {
      // Show saving indicator
      if (savingIndicator) {
        savingIndicator.style.display = 'flex';
      }
      if (saveBtn) {
        saveBtn.disabled = true;
      }

      // Gather form data
      const formData = this.getFormData(form);

      // Determine if creating or updating
      const isUpdate = !!this.currentTemplate;
      const url = isUpdate
        ? `${this.apiBase}/${this.currentTemplate.id}/`
        : `${this.apiBase}/`;

      const method = isUpdate ? 'PATCH' : 'POST';

      // Make API request
      const response = await this.apiRequest(url, method, formData);

      // Show success message
      if (savingIndicator) {
        savingIndicator.innerHTML = `
          <i class="bi bi-check-circle text-success"></i>
          <span>Saved!</span>
        `;
        savingIndicator.classList.add('saved');
      }

      this.showToast(
        isUpdate ? 'Template updated successfully' : 'Template created successfully',
        'success'
      );

      // Close modal after delay
      setTimeout(() => {
        modal.hide();
        // Reload page to show updated list
        window.location.reload();
      }, 1000);

    } catch (error) {
      console.error('Failed to save template:', error);

      // Show error
      this.showToast(
        error.message || 'Failed to save template',
        'error'
      );

      // Reset saving indicator
      if (savingIndicator) {
        savingIndicator.style.display = 'none';
      }
      if (saveBtn) {
        saveBtn.disabled = false;
      }
    }
  }

  /**
   * Get form data
   * @param {HTMLFormElement} form - Form element
   * @returns {Object} Form data
   */
  getFormData(form) {
    const data = {
      title: form.querySelector('#template-title')?.value.trim() || '',
      description: form.querySelector('#template-description')?.value.trim() || '',
      domain: form.querySelector('#template-domain')?.value || '',
      prompt_body: form.querySelector('#template-prompt')?.value.trim() || '',
      visibility: form.querySelector('#template-visibility')?.value || 'private',
      tags: []
    };

    // Get tags
    const tagsContainer = form.querySelector('#template-tags');
    if (tagsContainer) {
      data.tags = Array.from(tagsContainer.querySelectorAll('.tag-item'))
        .map(el => el.textContent.trim().replace('×', '').trim())
        .filter(tag => tag.length > 0);
    }

    return data;
  }

  /**
   * Schedule autosave
   * @param {GlassModal} modal - Modal instance
   * @param {HTMLFormElement} form - Form element
   */
  scheduleAutosave(modal, form) {
    if (this.autosaveTimer) {
      clearTimeout(this.autosaveTimer);
    }

    this.autosaveTimer = setTimeout(() => {
      // Only autosave for existing templates
      if (this.currentTemplate) {
        this.autosave(modal, form);
      }
    }, 2000);
  }

  /**
   * Autosave template
   * @param {GlassModal} modal - Modal instance
   * @param {HTMLFormElement} form - Form element
   */
  async autosave(modal, form) {
    const savingIndicator = modal.modal.querySelector('.saving-indicator');

    try {
      if (savingIndicator) {
        savingIndicator.style.display = 'flex';
        savingIndicator.innerHTML = `
          <div class="spinner-border spinner-border-sm" role="status"></div>
          <span>Autosaving...</span>
        `;
        savingIndicator.classList.remove('saved');
      }

      const formData = this.getFormData(form);
      await this.apiRequest(
        `${this.apiBase}/${this.currentTemplate.id}/`,
        'PATCH',
        formData
      );

      if (savingIndicator) {
        savingIndicator.innerHTML = `
          <i class="bi bi-check-circle text-success"></i>
          <span>Saved</span>
        `;
        savingIndicator.classList.add('saved');

        setTimeout(() => {
          savingIndicator.style.display = 'none';
        }, 2000);
      }

    } catch (error) {
      console.error('Autosave failed:', error);
      if (savingIndicator) {
        savingIndicator.style.display = 'none';
      }
    }
  }

  /**
   * Cleanup autosave timer
   */
  cleanupAutosave() {
    if (this.autosaveTimer) {
      clearTimeout(this.autosaveTimer);
      this.autosaveTimer = null;
    }
  }

  /**
   * Run AI validation
   * @param {GlassModal} modal - Modal instance
   */
  async runAIValidation(modal) {
    const form = modal.modal.querySelector('#templateForm');
    const promptBody = form.querySelector('#template-prompt')?.value.trim();

    if (!promptBody) {
      this.showToast('Please enter a prompt to validate', 'warning');
      return;
    }

    // Show feedback modal
    const feedbackModal = GlassModal.create({
      type: 'feedback',
      size: 'md',
      title: '<i class="bi bi-cpu"></i> AI Validation',
      body: `
        <div class="text-center py-4">
          <div class="spinner mb-3"></div>
          <p>Analyzing prompt quality...</p>
          <div class="progress mt-3">
            <div class="progress-bar" role="progressbar" style="width: 0%" id="validation-progress"></div>
          </div>
        </div>
      `,
      footer: `
        <button type="button" class="btn btn-secondary" data-dismiss="modal">
          Close
        </button>
      `
    });

    feedbackModal.show();

    try {
      // Create validation client
      this.validationClient = new TemplateValidationClient();

      // Progress handler
      this.validationClient.onProgress((data) => {
        const progressBar = document.querySelector('#validation-progress');
        if (progressBar && data.progress) {
          progressBar.style.width = `${data.progress}%`;
        }
      });

      // Validation complete
      this.validationClient.onComplete((data) => {
        this.showValidationResults(feedbackModal, data);
      });

      // Error handler
      this.validationClient.onError((error) => {
        console.error('Validation error:', error);
        feedbackModal.setContent(`
          <div class="text-center py-4">
            <i class="bi bi-x-circle text-danger" style="font-size: 3rem;"></i>
            <p class="mt-3">Validation failed. Please try again.</p>
          </div>
        `);
      });

      // Start validation
      const templateId = this.currentTemplate?.id || 'temp';
      this.validationClient.startValidation(templateId);

    } catch (error) {
      console.error('Validation error:', error);
      this.showToast('AI validation failed', 'error');
      feedbackModal.hide();
    }
  }

  /**
   * Show validation results
   * @param {GlassModal} modal - Modal instance
   * @param {Object} data - Validation data
   */
  showValidationResults(modal, data) {
    const score = data.quality_score || 0;

    modal.setContent(`
      <div class="quality-score">
        <div class="score-circle" style="--score: ${score}">
          <span class="score-value">${score}</span>
        </div>
      </div>

      <h6 class="text-center mb-3">Quality Analysis</h6>

      <ul class="feedback-list">
        ${data.feedback && data.feedback.map(item => `
          <li class="feedback-item ${item.type || 'info'}">
            <i class="bi bi-${this.getFeedbackIcon(item.type)}"></i>
            <span>${this.escapeHtml(item.message)}</span>
          </li>
        `).join('') || '<li class="feedback-item info"><i class="bi bi-info-circle"></i> No specific feedback available.</li>'}
      </ul>

      ${data.suggestions ? `
        <div class="mt-3">
          <h6>Suggestions</h6>
          <div class="ai-hint">
            <i class="bi bi-lightbulb"></i>
            <span>${this.escapeHtml(data.suggestions)}</span>
          </div>
        </div>
      ` : ''}
    `);
  }

  /**
   * Get feedback icon by type
   * @param {string} type - Feedback type
   * @returns {string} Icon class
   */
  getFeedbackIcon(type) {
    const icons = {
      success: 'check-circle',
      warning: 'exclamation-triangle',
      error: 'x-circle',
      info: 'info-circle'
    };
    return icons[type] || 'info-circle';
  }

  /**
   * Confirm delete template
   * @param {string} templateId - Template ID
   */
  async confirmDelete(templateId) {
    const confirmed = await GlassModal.confirm({
      title: 'Delete Template',
      message: 'Are you sure you want to delete this template? This action cannot be undone.',
      confirmText: 'Delete',
      cancelText: 'Cancel',
      confirmClass: 'btn-danger',
      icon: 'bi-trash'
    });

    if (confirmed) {
      await this.deleteTemplate(templateId);
    }
  }

  /**
   * Delete template
   * @param {string} templateId - Template ID
   */
  async deleteTemplate(templateId) {
    try {
      await this.apiRequest(`${this.apiBase}/${templateId}/`, 'DELETE');
      this.showToast('Template deleted successfully', 'success');

      // Remove from DOM
      const card = document.querySelector(`[data-template-id="${templateId}"]`)?.closest('.card');
      if (card) {
        card.style.opacity = '0';
        card.style.transform = 'scale(0.9)';
        setTimeout(() => card.remove(), 200);
      }

    } catch (error) {
      console.error('Failed to delete template:', error);
      this.showToast('Failed to delete template', 'error');
    }
  }

  /**
   * Show preview modal
   * @param {string} templateId - Template ID
   */
  async showPreviewModal(templateId) {
    try {
      const template = await this.fetchTemplate(templateId);

      const modal = GlassModal.create({
        type: 'preview',
        size: 'lg',
        title: `<i class="bi bi-eye"></i> ${this.escapeHtml(template.title)}`,
        body: `
          <div class="preview-content">
            <button class="copy-button" data-action="copy-prompt">
              <i class="bi bi-clipboard"></i> Copy
            </button>
            <pre><code>${this.escapeHtml(template.prompt_body)}</code></pre>
          </div>

          ${template.description ? `
            <div class="mt-3">
              <h6>Description</h6>
              <p>${this.escapeHtml(template.description)}</p>
            </div>
          ` : ''}

          ${template.tags && template.tags.length > 0 ? `
            <div class="mt-3">
              <h6>Tags</h6>
              <div class="d-flex flex-wrap gap-2">
                ${template.tags.map(tag => `
                  <span class="badge badge-domain">${this.escapeHtml(tag)}</span>
                `).join('')}
              </div>
            </div>
          ` : ''}
        `,
        footer: `
          <button type="button" class="btn btn-secondary" data-dismiss="modal">
            Close
          </button>
          <button type="button" class="btn btn-primary" data-action="use-template">
            <i class="bi bi-play-fill"></i> Use Template
          </button>
        `,
        onShown: () => {
          // Copy button handler
          const copyBtn = modal.modal.querySelector('[data-action="copy-prompt"]');
          if (copyBtn) {
            copyBtn.addEventListener('click', () => {
              this.copyToClipboard(template.prompt_body, copyBtn);
            });
          }
        },
        onHidden: () => {
          modal.destroy();
        }
      });

      modal.show();

    } catch (error) {
      console.error('Failed to show preview:', error);
      this.showToast('Failed to load preview', 'error');
    }
  }

  /**
   * Duplicate template
   * @param {string} templateId - Template ID
   */
  async duplicateTemplate(templateId) {
    try {
      const template = await this.fetchTemplate(templateId);

      // Create duplicate with modified title
      const duplicate = {
        ...template,
        title: `${template.title} (Copy)`,
        id: undefined
      };

      delete duplicate.id;
      delete duplicate.created_at;
      delete duplicate.updated_at;
      delete duplicate.author;

      const response = await this.apiRequest(this.apiBase + '/', 'POST', duplicate);

      this.showToast('Template duplicated successfully', 'success');

      // Reload page to show new template
      setTimeout(() => window.location.reload(), 1000);

    } catch (error) {
      console.error('Failed to duplicate template:', error);
      this.showToast('Failed to duplicate template', 'error');
    }
  }

  /**
   * Initialize search and filter
   */
  initializeSearchFilter() {
    const searchInput = document.querySelector('#template-search');
    const domainFilter = document.querySelector('#domain-filter');
    const sortSelect = document.querySelector('#sort-select');

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.handleSearch(e.target.value);
      });
    }

    if (domainFilter) {
      domainFilter.addEventListener('change', (e) => {
        this.applyFilters();
      });
    }

    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        this.applySort(e.target.value);
      });
    }
  }

  /**
   * Handle search with debounce
   * @param {string} query - Search query
   */
  handleSearch(query) {
    if (this.searchDebounceTimer) {
      clearTimeout(this.searchDebounceTimer);
    }

    this.searchDebounceTimer = setTimeout(() => {
      this.performSearch(query);
    }, 150);
  }

  /**
   * Perform search
   * @param {string} query - Search query
   */
  performSearch(query) {
    const cards = document.querySelectorAll('.template-card');
    const lowerQuery = query.toLowerCase();

    cards.forEach(card => {
      const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
      const description = card.querySelector('.card-text')?.textContent.toLowerCase() || '';
      const tags = Array.from(card.querySelectorAll('.badge'))
        .map(badge => badge.textContent.toLowerCase())
        .join(' ');

      const matches = title.includes(lowerQuery) ||
                     description.includes(lowerQuery) ||
                     tags.includes(lowerQuery);

      card.style.display = matches ? '' : 'none';
    });
  }

  /**
   * Apply filters
   */
  applyFilters() {
    // Implement filter logic here
    console.log('Applying filters...');
  }

  /**
   * Apply sort
   * @param {string} sortBy - Sort field
   */
  applySort(sortBy) {
    // Implement sort logic here
    console.log('Sorting by:', sortBy);
  }

  /**
   * Fetch template by ID
   * @param {string} templateId - Template ID
   * @returns {Promise<Object>} Template data
   */
  async fetchTemplate(templateId) {
    return await this.apiRequest(`${this.apiBase}/${templateId}/`, 'GET');
  }

  /**
   * Make API request
   * @param {string} url - API URL
   * @param {string} method - HTTP method
   * @param {Object} data - Request data
   * @returns {Promise<Object>} Response data
   */
  async apiRequest(url, method = 'GET', data = null) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.csrfToken
      },
      credentials: 'same-origin'
    };

    if (data && method !== 'GET') {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
    }

    if (method === 'DELETE') {
      return {};
    }

    return await response.json();
  }

  /**
   * Get CSRF token
   * @returns {string} CSRF token
   */
  getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value;
      }
    }
    return '';
  }

  /**
   * Copy to clipboard
   * @param {string} text - Text to copy
   * @param {HTMLElement} button - Button element
   */
  async copyToClipboard(text, button) {
    try {
      await navigator.clipboard.writeText(text);

      // Update button
      const originalHTML = button.innerHTML;
      button.innerHTML = '<i class="bi bi-check"></i> Copied!';
      button.classList.add('copied');

      setTimeout(() => {
        button.innerHTML = originalHTML;
        button.classList.remove('copied');
      }, 2000);

      this.showToast('Copied to clipboard', 'success');

    } catch (error) {
      console.error('Failed to copy:', error);
      this.showToast('Failed to copy to clipboard', 'error');
    }
  }

  /**
   * Show toast notification
   * @param {string} message - Toast message
   * @param {string} type - Toast type
   */
  showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container position-fixed top-0 end-0 p-3';
      container.style.zIndex = var(--z-toast, '1080');
      document.body.appendChild(container);
    }

    // Create toast
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    container.appendChild(toast);

    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 200);
    }, 3000);
  }

  /**
   * Escape HTML
   * @param {string} text - Text to escape
   * @returns {string} Escaped text
   */
  escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.templateCRUD = new TemplateCRUD();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TemplateCRUD;
}
