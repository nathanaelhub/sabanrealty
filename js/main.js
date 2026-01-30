/* ===============================================
   SABAN REALTY - JavaScript
   =============================================== */

document.addEventListener('DOMContentLoaded', function() {
  
  // ---- Mobile Navigation ----
  const navToggle = document.querySelector('.nav-toggle');
  const navMenu = document.querySelector('.nav-menu');
  const navClose = document.querySelector('.nav-close');
  const navLinks = document.querySelectorAll('.nav-link');

  if (navToggle) {
    navToggle.addEventListener('click', () => {
      navMenu.classList.add('active');
      document.body.style.overflow = 'hidden';
    });
  }

  if (navClose) {
    navClose.addEventListener('click', () => {
      navMenu.classList.remove('active');
      document.body.style.overflow = '';
    });
  }

  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      navMenu.classList.remove('active');
      document.body.style.overflow = '';
    });
  });

  // ---- Navbar Scroll Effect ----
  const navbar = document.querySelector('.navbar');
  
  function handleNavbarScroll() {
    if (window.scrollY > 100) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }

  window.addEventListener('scroll', handleNavbarScroll);
  handleNavbarScroll(); // Run on page load

  // ---- Scroll to Top Button ----
  const scrollTopBtn = document.querySelector('.scroll-top');
  
  if (scrollTopBtn) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 500) {
        scrollTopBtn.classList.add('active');
      } else {
        scrollTopBtn.classList.remove('active');
      }
    });

    scrollTopBtn.addEventListener('click', () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    });
  }

  // ---- Smooth Scroll for Anchor Links ----
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offsetTop = target.offsetTop - 80; // Account for fixed navbar
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }
    });
  });

  // ---- Fade In Animation on Scroll ----
  const fadeElements = document.querySelectorAll('.fade-in');
  
  const fadeInObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        fadeInObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });

  fadeElements.forEach(el => fadeInObserver.observe(el));

  // ---- Property Filtering ----
  const filterForm = document.querySelector('.filter-bar');
  const propertyGrid = document.querySelector('.property-grid');
  
  if (filterForm && propertyGrid) {
    const propertyTypeFilter = document.getElementById('propertyType');
    const bedroomsFilter = document.getElementById('bedrooms');
    const priceFilter = document.getElementById('priceRange');
    const searchInput = document.getElementById('searchInput');

    function filterProperties() {
      const cards = propertyGrid.querySelectorAll('.property-card');
      const propertyType = propertyTypeFilter?.value || 'all';
      const bedrooms = bedroomsFilter?.value || 'all';
      const price = priceFilter?.value || 'all';
      const searchTerm = searchInput?.value.toLowerCase() || '';

      cards.forEach(card => {
        const cardType = card.dataset.type || '';
        const cardBedrooms = card.dataset.bedrooms || '';
        const cardPrice = parseInt(card.dataset.price) || 0;
        const cardTitle = card.querySelector('.property-title')?.textContent.toLowerCase() || '';
        const cardLocation = card.querySelector('.property-location')?.textContent.toLowerCase() || '';

        let showCard = true;

        // Property Type Filter
        if (propertyType !== 'all' && cardType !== propertyType) {
          showCard = false;
        }

        // Bedrooms Filter
        if (bedrooms !== 'all' && cardBedrooms !== bedrooms) {
          showCard = false;
        }

        // Price Filter
        if (price !== 'all') {
          const [minPrice, maxPrice] = price.split('-').map(p => parseInt(p) || Infinity);
          if (cardPrice < minPrice || cardPrice > maxPrice) {
            showCard = false;
          }
        }

        // Search Filter
        if (searchTerm && !cardTitle.includes(searchTerm) && !cardLocation.includes(searchTerm)) {
          showCard = false;
        }

        card.style.display = showCard ? 'block' : 'none';
      });

      // Check if no results
      const visibleCards = propertyGrid.querySelectorAll('.property-card[style="display: block;"], .property-card:not([style*="display"])');
      const noResults = document.querySelector('.no-results');
      
      if (visibleCards.length === 0) {
        if (!noResults) {
          const noResultsMsg = document.createElement('div');
          noResultsMsg.className = 'no-results';
          noResultsMsg.innerHTML = '<p>No properties found matching your criteria. Try adjusting your filters.</p>';
          propertyGrid.appendChild(noResultsMsg);
        }
      } else if (noResults) {
        noResults.remove();
      }
    }

    // Add event listeners to filters
    propertyTypeFilter?.addEventListener('change', filterProperties);
    bedroomsFilter?.addEventListener('change', filterProperties);
    priceFilter?.addEventListener('change', filterProperties);
    searchInput?.addEventListener('input', filterProperties);
  }

  // ---- Form Validation ----
  const forms = document.querySelectorAll('form[data-validate]');
  
  forms.forEach(form => {
    form.addEventListener('submit', function(e) {
      e.preventDefault();
      
      let isValid = true;
      const requiredFields = form.querySelectorAll('[required]');
      
      requiredFields.forEach(field => {
        removeError(field);
        
        if (!field.value.trim()) {
          showError(field, 'This field is required');
          isValid = false;
        } else if (field.type === 'email' && !isValidEmail(field.value)) {
          showError(field, 'Please enter a valid email address');
          isValid = false;
        } else if (field.type === 'tel' && !isValidPhone(field.value)) {
          showError(field, 'Please enter a valid phone number');
          isValid = false;
        }
      });
      
      if (isValid) {
        // Show success message
        showFormSuccess(form);
        form.reset();
      }
    });
  });

  function showError(field, message) {
    field.classList.add('error');
    const errorEl = document.createElement('span');
    errorEl.className = 'error-message';
    errorEl.textContent = message;
    errorEl.style.cssText = 'color: #e07a5f; font-size: 0.875rem; margin-top: 0.25rem; display: block;';
    field.parentNode.appendChild(errorEl);
  }

  function removeError(field) {
    field.classList.remove('error');
    const errorEl = field.parentNode.querySelector('.error-message');
    if (errorEl) errorEl.remove();
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function isValidPhone(phone) {
    return /^[\d\s\-\+\(\)]{10,}$/.test(phone);
  }

  function showFormSuccess(form) {
    const successMsg = document.createElement('div');
    successMsg.className = 'form-success';
    successMsg.innerHTML = `
      <div style="background: #27ae60; color: white; padding: 1rem; border-radius: 8px; margin-top: 1rem; text-align: center;">
        <strong>Thank you!</strong> Your message has been sent successfully. We'll get back to you soon.
      </div>
    `;
    form.appendChild(successMsg);
    
    setTimeout(() => {
      successMsg.remove();
    }, 5000);
  }

  // ---- Property Image Gallery (for detail pages) ----
  const galleryImages = document.querySelectorAll('.gallery-thumb');
  const mainImage = document.querySelector('.gallery-main img');
  
  if (galleryImages.length && mainImage) {
    galleryImages.forEach(thumb => {
      thumb.addEventListener('click', function() {
        const newSrc = this.querySelector('img').src;
        mainImage.src = newSrc;
        
        galleryImages.forEach(t => t.classList.remove('active'));
        this.classList.add('active');
      });
    });
  }

  // ---- Dark Mode Toggle ----
  const themeToggle = document.querySelector('.theme-toggle');
  
  if (themeToggle) {
    // Check for saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      document.documentElement.setAttribute('data-theme', savedTheme);
      updateThemeIcon(savedTheme);
    }

    themeToggle.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme');
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('theme', newTheme);
      updateThemeIcon(newTheme);
    });
  }

  function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-toggle svg');
    if (icon) {
      if (theme === 'dark') {
        icon.innerHTML = '<path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
      } else {
        icon.innerHTML = '<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>';
      }
    }
  }

  // ---- Newsletter Form ----
  const newsletterForm = document.querySelector('.newsletter-form');
  
  if (newsletterForm) {
    newsletterForm.addEventListener('submit', function(e) {
      e.preventDefault();
      const email = this.querySelector('input[type="email"]');
      
      if (email && isValidEmail(email.value)) {
        this.innerHTML = '<p style="color: #27ae60; font-weight: 600;">Thank you for subscribing!</p>';
      }
    });
  }

  // ---- Lazy Loading Images ----
  const lazyImages = document.querySelectorAll('img[data-src]');
  
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          imageObserver.unobserve(img);
        }
      });
    });

    lazyImages.forEach(img => imageObserver.observe(img));
  } else {
    // Fallback for older browsers
    lazyImages.forEach(img => {
      img.src = img.dataset.src;
    });
  }

  // ---- Active Navigation Link ----
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const navLinksAll = document.querySelectorAll('.nav-link');
  
  navLinksAll.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

});

// ---- Property Data (for static site - can be replaced with JSON file) ----
const propertyData = {
  properties: [
    // This array would be populated from a JSON file or CMS
    // Example structure shown in the HTML files
  ]
};
