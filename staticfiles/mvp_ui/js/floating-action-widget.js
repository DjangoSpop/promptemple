/**
 * Floating Action Widget Controller
 * Manages the floating action button and quick navigation menu
 */

class FloatingActionWidget {
  constructor() {
    this.widget = null;
    this.mainButton = null;
    this.backdrop = null;
    this.isOpen = false;

    this.init();
  }

  /**
   * Initialize widget
   */
  init() {
    // Create widget if it doesn't exist
    if (!document.querySelector('.floating-action-widget')) {
      this.createWidget();
    } else {
      this.widget = document.querySelector('.floating-action-widget');
      this.mainButton = this.widget.querySelector('.fab-main');
    }

    this.bindEvents();
  }

  /**
   * Create widget HTML
   */
  createWidget() {
    const widget = document.createElement('div');
    widget.className = 'floating-action-widget';
    widget.innerHTML = `
      <div class="fab-menu">
        <a href="/templates/" class="fab-menu-item" data-tooltip="Browse Templates">
          <span class="fab-menu-label">Templates</span>
          <button type="button" class="fab-menu-btn templates">
            <i class="bi bi-file-text"></i>
          </button>
        </a>

        <a href="/ai-services/" class="fab-menu-item" data-tooltip="AI Optimizer">
          <span class="fab-menu-label">AI Optimizer</span>
          <button type="button" class="fab-menu-btn optimizer">
            <i class="bi bi-cpu"></i>
          </button>
        </a>

        <a href="/research/" class="fab-menu-item" data-tooltip="Research">
          <span class="fab-menu-label">Research</span>
          <button type="button" class="fab-menu-btn research">
            <i class="bi bi-search"></i>
          </button>
        </a>

        <a href="/dashboard/" class="fab-menu-item" data-tooltip="Dashboard">
          <span class="fab-menu-label">Dashboard</span>
          <button type="button" class="fab-menu-btn dashboard">
            <i class="bi bi-speedometer2"></i>
          </button>
        </a>
      </div>

      <button type="button" class="fab-main" aria-label="Quick Actions Menu" aria-expanded="false">
        <i class="bi bi-plus-lg"></i>
      </button>
    `;

    document.body.appendChild(widget);

    // Create backdrop for mobile
    const backdrop = document.createElement('div');
    backdrop.className = 'fab-backdrop';
    document.body.appendChild(backdrop);

    this.widget = widget;
    this.mainButton = widget.querySelector('.fab-main');
    this.backdrop = backdrop;
  }

  /**
   * Bind event listeners
   */
  bindEvents() {
    // Main button toggle
    this.mainButton.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggle();
    });

    // Close on backdrop click
    if (this.backdrop) {
      this.backdrop.addEventListener('click', () => {
        this.close();
      });
    }

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen) {
        this.close();
      }
    });

    // Close when clicking outside
    document.addEventListener('click', (e) => {
      if (this.isOpen && !this.widget.contains(e.target)) {
        this.close();
      }
    });

    // Prevent menu items from closing widget when using keyboard
    const menuItems = this.widget.querySelectorAll('.fab-menu-item');
    menuItems.forEach(item => {
      item.addEventListener('click', () => {
        // Let navigation happen
        this.close();
      });
    });
  }

  /**
   * Toggle widget open/close
   */
  toggle() {
    if (this.isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  /**
   * Open widget
   */
  open() {
    this.widget.classList.add('active');
    this.mainButton.setAttribute('aria-expanded', 'true');
    this.isOpen = true;

    // Add active class to body to prevent scroll on mobile
    if (window.innerWidth <= 768) {
      document.body.classList.add('fab-open');
    }
  }

  /**
   * Close widget
   */
  close() {
    this.widget.classList.remove('active');
    this.mainButton.setAttribute('aria-expanded', 'false');
    this.isOpen = false;

    document.body.classList.remove('fab-open');
  }

  /**
   * Add notification badge to menu item
   * @param {string} itemClass - Menu item class (templates, optimizer, research, dashboard)
   * @param {number} count - Notification count
   */
  addNotification(itemClass, count) {
    const menuItem = this.widget.querySelector(`.fab-menu-btn.${itemClass}`);
    if (!menuItem) return;

    // Remove existing badge
    const existingBadge = menuItem.querySelector('.notification-badge');
    if (existingBadge) {
      existingBadge.remove();
    }

    // Add new badge if count > 0
    if (count > 0) {
      const badge = document.createElement('span');
      badge.className = 'notification-badge';
      badge.textContent = count > 9 ? '9+' : count;
      menuItem.appendChild(badge);
    }
  }

  /**
   * Remove notification badge
   * @param {string} itemClass - Menu item class
   */
  removeNotification(itemClass) {
    const menuItem = this.widget.querySelector(`.fab-menu-btn.${itemClass}`);
    if (!menuItem) return;

    const badge = menuItem.querySelector('.notification-badge');
    if (badge) {
      badge.remove();
    }
  }

  /**
   * Update menu item URL
   * @param {string} itemClass - Menu item class
   * @param {string} url - New URL
   */
  updateItemUrl(itemClass, url) {
    const menuItem = this.widget.querySelector(`.fab-menu-btn.${itemClass}`).closest('.fab-menu-item');
    if (menuItem) {
      menuItem.href = url;
    }
  }

  /**
   * Show/hide widget
   * @param {boolean} show - Show or hide
   */
  setVisible(show) {
    if (show) {
      this.widget.style.display = '';
    } else {
      this.widget.style.display = 'none';
      this.close();
    }
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.floatingActionWidget = new FloatingActionWidget();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FloatingActionWidget;
}
