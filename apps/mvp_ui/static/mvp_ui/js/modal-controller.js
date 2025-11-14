/**
 * GlassModal Controller
 * Enterprise-grade modal management with accessibility and keyboard navigation
 *
 * Features:
 * - Keyboard navigation (Esc, Tab, Shift+Tab)
 * - Focus trap and management
 * - ARIA compliance
 * - Multiple instances support
 * - Event hooks for custom behavior
 * - Mobile-optimized (virtual keyboard detection)
 * - Stack management for nested modals
 */

class GlassModal {
  /**
   * Create a new GlassModal instance
   * @param {string|HTMLElement} element - Modal element or selector
   * @param {Object} options - Configuration options
   */
  constructor(element, options = {}) {
    // Get modal element
    this.modal = typeof element === 'string'
      ? document.querySelector(element)
      : element;

    if (!this.modal) {
      console.error('GlassModal: Element not found');
      return;
    }

    // Configuration
    this.options = {
      keyboard: true,           // Allow Esc to close
      backdrop: true,           // Show backdrop
      focus: true,              // Auto-focus on open
      closeOnBackdrop: true,    // Close when clicking backdrop
      scrollable: true,         // Allow body scrolling when open
      onShow: null,             // Callback when modal shows
      onShown: null,            // Callback after modal shown
      onHide: null,             // Callback when modal hides
      onHidden: null,           // Callback after modal hidden
      ...options
    };

    // State
    this.isOpen = false;
    this.previouslyFocusedElement = null;
    this.focusableElements = [];
    this.firstFocusableElement = null;
    this.lastFocusableElement = null;

    // Initialize
    this.init();
  }

  /**
   * Initialize modal controller
   */
  init() {
    // Create backdrop if needed
    if (this.options.backdrop && !this.backdrop) {
      this.createBackdrop();
    }

    // Find modal components
    this.dialog = this.modal.querySelector('.modal-dialog');
    this.content = this.modal.querySelector('.modal-content');
    this.closeButtons = this.modal.querySelectorAll('[data-dismiss="modal"], .modal-close, .btn-close');

    // Set ARIA attributes
    this.modal.setAttribute('role', 'dialog');
    this.modal.setAttribute('aria-modal', 'true');
    this.modal.setAttribute('aria-hidden', 'true');

    // Bind events
    this.bindEvents();

    // Update focusable elements
    this.updateFocusableElements();
  }

  /**
   * Create backdrop element
   */
  createBackdrop() {
    this.backdrop = document.createElement('div');
    this.backdrop.className = 'modal-backdrop';
    this.backdrop.setAttribute('aria-hidden', 'true');
    document.body.appendChild(this.backdrop);
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Close buttons
    this.closeButtons.forEach(btn => {
      btn.addEventListener('click', () => this.hide());
    });

    // Backdrop click
    if (this.options.closeOnBackdrop) {
      this.modal.addEventListener('click', (e) => {
        if (e.target === this.modal) {
          this.hide();
        }
      });
    }

    // Keyboard events
    if (this.options.keyboard) {
      this.handleKeyDown = this.handleKeyDown.bind(this);
    }

    // Virtual keyboard detection (mobile)
    this.detectVirtualKeyboard();
  }

  /**
   * Show modal
   */
  show() {
    if (this.isOpen) return;

    // Fire onShow callback
    if (this.options.onShow) {
      this.options.onShow(this);
    }

    // Store currently focused element
    this.previouslyFocusedElement = document.activeElement;

    // Prevent body scroll
    if (!this.options.scrollable) {
      document.body.classList.add('modal-open');
    }

    // Show backdrop
    if (this.backdrop) {
      this.backdrop.classList.add('show');
    }

    // Show modal
    this.modal.classList.add('show');
    this.modal.setAttribute('aria-hidden', 'false');
    this.isOpen = true;

    // Update focusable elements
    this.updateFocusableElements();

    // Set focus
    if (this.options.focus && this.firstFocusableElement) {
      // Small delay to ensure modal is visible
      setTimeout(() => {
        this.firstFocusableElement.focus();
      }, 100);
    }

    // Add keyboard listener
    if (this.options.keyboard) {
      document.addEventListener('keydown', this.handleKeyDown);
    }

    // Fire onShown callback after transition
    setTimeout(() => {
      if (this.options.onShown) {
        this.options.onShown(this);
      }
    }, 200);

    // Add to modal stack
    GlassModal.stack.push(this);
  }

  /**
   * Hide modal
   */
  hide() {
    if (!this.isOpen) return;

    // Fire onHide callback
    if (this.options.onHide) {
      this.options.onHide(this);
    }

    // Hide modal
    this.modal.classList.remove('show');
    this.modal.setAttribute('aria-hidden', 'true');

    // Hide backdrop
    if (this.backdrop) {
      this.backdrop.classList.remove('show');
    }

    // Remove from modal stack
    const index = GlassModal.stack.indexOf(this);
    if (index > -1) {
      GlassModal.stack.splice(index, 1);
    }

    // Allow body scroll if no other modals
    if (GlassModal.stack.length === 0) {
      document.body.classList.remove('modal-open');
    }

    // Remove keyboard listener
    if (this.options.keyboard) {
      document.removeEventListener('keydown', this.handleKeyDown);
    }

    // Restore focus
    if (this.previouslyFocusedElement && this.previouslyFocusedElement.focus) {
      this.previouslyFocusedElement.focus();
    }

    this.isOpen = false;

    // Fire onHidden callback after transition
    setTimeout(() => {
      if (this.options.onHidden) {
        this.options.onHidden(this);
      }
    }, 200);
  }

  /**
   * Toggle modal visibility
   */
  toggle() {
    if (this.isOpen) {
      this.hide();
    } else {
      this.show();
    }
  }

  /**
   * Handle keyboard events
   * @param {KeyboardEvent} e - Keyboard event
   */
  handleKeyDown(e) {
    // Esc key - close modal
    if (e.key === 'Escape' || e.keyCode === 27) {
      e.preventDefault();
      this.hide();
      return;
    }

    // Tab key - focus trap
    if (e.key === 'Tab' || e.keyCode === 9) {
      this.handleTabKey(e);
    }
  }

  /**
   * Handle Tab key for focus trap
   * @param {KeyboardEvent} e - Keyboard event
   */
  handleTabKey(e) {
    if (this.focusableElements.length === 0) return;

    const isTabForward = !e.shiftKey;
    const activeElement = document.activeElement;

    // Forward tab on last element - go to first
    if (isTabForward && activeElement === this.lastFocusableElement) {
      e.preventDefault();
      this.firstFocusableElement.focus();
    }

    // Backward tab on first element - go to last
    if (!isTabForward && activeElement === this.firstFocusableElement) {
      e.preventDefault();
      this.lastFocusableElement.focus();
    }
  }

  /**
   * Update list of focusable elements
   */
  updateFocusableElements() {
    const focusableSelectors = [
      'a[href]',
      'button:not([disabled])',
      'textarea:not([disabled])',
      'input:not([disabled]):not([type="hidden"])',
      'select:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable="true"]'
    ];

    this.focusableElements = Array.from(
      this.modal.querySelectorAll(focusableSelectors.join(','))
    ).filter(el => {
      return el.offsetWidth > 0 &&
             el.offsetHeight > 0 &&
             !el.hasAttribute('hidden');
    });

    this.firstFocusableElement = this.focusableElements[0];
    this.lastFocusableElement = this.focusableElements[this.focusableElements.length - 1];
  }

  /**
   * Detect virtual keyboard (mobile)
   */
  detectVirtualKeyboard() {
    let initialHeight = window.innerHeight;

    window.addEventListener('resize', () => {
      const currentHeight = window.innerHeight;
      const isKeyboardVisible = currentHeight < initialHeight * 0.8;

      if (isKeyboardVisible) {
        this.modal.classList.add('keyboard-visible');
      } else {
        this.modal.classList.remove('keyboard-visible');
        initialHeight = currentHeight;
      }
    });
  }

  /**
   * Update modal content
   * @param {string} content - HTML content
   */
  setContent(content) {
    const body = this.modal.querySelector('.modal-body');
    if (body) {
      body.innerHTML = content;
      this.updateFocusableElements();
    }
  }

  /**
   * Set modal title
   * @param {string} title - Modal title
   */
  setTitle(title) {
    const titleEl = this.modal.querySelector('.modal-title');
    if (titleEl) {
      titleEl.textContent = title;
    }
  }

  /**
   * Destroy modal instance
   */
  destroy() {
    this.hide();

    if (this.backdrop) {
      this.backdrop.remove();
    }

    // Remove event listeners
    if (this.options.keyboard) {
      document.removeEventListener('keydown', this.handleKeyDown);
    }

    // Remove from instances
    const index = GlassModal.instances.indexOf(this);
    if (index > -1) {
      GlassModal.instances.splice(index, 1);
    }
  }
}

// Static properties
GlassModal.instances = [];
GlassModal.stack = [];

/**
 * Get or create modal instance
 * @param {string|HTMLElement} element - Modal element or selector
 * @param {Object} options - Configuration options
 * @returns {GlassModal} Modal instance
 */
GlassModal.getInstance = function(element, options = {}) {
  const el = typeof element === 'string' ? document.querySelector(element) : element;

  // Check if instance already exists
  const existing = GlassModal.instances.find(instance => instance.modal === el);
  if (existing) {
    return existing;
  }

  // Create new instance
  const instance = new GlassModal(el, options);
  GlassModal.instances.push(instance);
  return instance;
};

/**
 * Hide all open modals
 */
GlassModal.hideAll = function() {
  GlassModal.stack.forEach(modal => modal.hide());
};

/**
 * Create modal from template
 * @param {Object} config - Modal configuration
 * @returns {GlassModal} Modal instance
 */
GlassModal.create = function(config) {
  const {
    id = `modal-${Date.now()}`,
    title = '',
    body = '',
    footer = '',
    size = '', // sm, lg, xl, fullscreen
    type = '', // template, delete, preview, feedback
    className = '',
    ...options
  } = config;

  // Create modal HTML
  const modal = document.createElement('div');
  modal.className = `modal modal-${type}`;
  modal.id = id;
  modal.setAttribute('tabindex', '-1');

  const sizeClass = size ? `modal-dialog-${size}` : '';

  modal.innerHTML = `
    <div class="modal-dialog ${sizeClass}">
      <div class="modal-content ${className}">
        ${title ? `
          <div class="modal-header">
            <h5 class="modal-title">${title}</h5>
            <button type="button" class="btn-close" data-dismiss="modal" aria-label="Close">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
        ` : ''}
        <div class="modal-body">
          ${body}
        </div>
        ${footer ? `
          <div class="modal-footer">
            ${footer}
          </div>
        ` : ''}
      </div>
    </div>
  `;

  // Append to body
  document.body.appendChild(modal);

  // Create instance
  return GlassModal.getInstance(modal, options);
};

/**
 * Show confirmation modal
 * @param {Object} config - Configuration
 * @returns {Promise<boolean>} User confirmation
 */
GlassModal.confirm = function(config) {
  return new Promise((resolve) => {
    const {
      title = 'Confirm Action',
      message = 'Are you sure?',
      confirmText = 'Confirm',
      cancelText = 'Cancel',
      confirmClass = 'btn-primary',
      icon = 'bi-exclamation-triangle'
    } = config;

    const modal = GlassModal.create({
      type: 'delete',
      size: 'sm',
      title,
      body: `
        <div class="delete-icon">
          <i class="bi ${icon}"></i>
        </div>
        <p class="text-center mb-0">${message}</p>
      `,
      footer: `
        <button type="button" class="btn btn-secondary" data-action="cancel">
          ${cancelText}
        </button>
        <button type="button" class="btn ${confirmClass}" data-action="confirm">
          ${confirmText}
        </button>
      `,
      onHidden: () => {
        modal.destroy();
        resolve(false);
      }
    });

    // Handle button clicks
    modal.modal.querySelector('[data-action="cancel"]').addEventListener('click', () => {
      modal.hide();
      resolve(false);
    });

    modal.modal.querySelector('[data-action="confirm"]').addEventListener('click', () => {
      modal.hide();
      resolve(true);
    });

    modal.show();
  });
};

/**
 * Show alert modal
 * @param {Object} config - Configuration
 */
GlassModal.alert = function(config) {
  const {
    title = 'Alert',
    message = '',
    type = 'info', // success, warning, error, info
    okText = 'OK'
  } = config;

  const icons = {
    success: 'bi-check-circle',
    warning: 'bi-exclamation-triangle',
    error: 'bi-x-circle',
    info: 'bi-info-circle'
  };

  const modal = GlassModal.create({
    type: 'feedback',
    size: 'sm',
    title,
    body: `
      <div class="text-center">
        <i class="bi ${icons[type]} text-${type}" style="font-size: 3rem;"></i>
        <p class="mt-3">${message}</p>
      </div>
    `,
    footer: `
      <button type="button" class="btn btn-primary" data-dismiss="modal">
        ${okText}
      </button>
    `,
    onHidden: () => {
      modal.destroy();
    }
  });

  modal.show();
};

// Auto-initialize modals with data attributes
document.addEventListener('DOMContentLoaded', () => {
  // Initialize modals with data-toggle="modal"
  document.querySelectorAll('[data-toggle="modal"]').forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const target = trigger.getAttribute('data-target') || trigger.getAttribute('href');
      if (target) {
        const modal = GlassModal.getInstance(target);
        modal.show();
      }
    });
  });

  // Auto-initialize existing modals
  document.querySelectorAll('.modal').forEach(modalEl => {
    GlassModal.getInstance(modalEl);
  });
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GlassModal;
}

// Global access
window.GlassModal = GlassModal;
