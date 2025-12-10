// static/js/cookies.js
// Gestión de cookies en el lado del cliente

document.addEventListener('DOMContentLoaded', function() {
    // Verificar si ya se ha dado consentimiento
    checkCookieConsent();
    
    // Inicializar banner de cookies
    initCookieBanner();
    
    // Inicializar configuración de cookies
    initCookieSettings();
    
    // Configurar cookies técnicas
    setupTechnicalCookies();
});

function checkCookieConsent() {
    // Verificar consentimiento en localStorage
    const consentGiven = localStorage.getItem('cookie_consent_given');
    const consentDate = localStorage.getItem('cookie_consent_date');
    
    if (!consentGiven) {
        // Mostrar banner si no hay consentimiento
        showCookieBanner();
    } else {
        // Configurar cookies según preferencias guardadas
        applyCookieSettings();
    }
}

function showCookieBanner() {
    const banner = document.getElementById('cookieConsentBanner');
    if (banner) {
        banner.style.display = 'block';
        
        // Animación de entrada
        setTimeout(() => {
            banner.style.opacity = '1';
            banner.style.transform = 'translateY(0)';
        }, 100);
    }
}

function hideCookieBanner() {
    const banner = document.getElementById('cookieConsentBanner');
    if (banner) {
        banner.style.opacity = '0';
        banner.style.transform = 'translateY(100%)';
        
        setTimeout(() => {
            banner.style.display = 'none';
        }, 300);
    }
}

function initCookieBanner() {
    // Botón para aceptar todas las cookies
    const acceptBtn = document.getElementById('acceptCookiesBtn');
    if (acceptBtn) {
        acceptBtn.addEventListener('click', function() {
            acceptAllCookies();
            hideCookieBanner();
        });
    }
    
    // Botón para rechazar cookies no esenciales
    const rejectBtn = document.getElementById('rejectCookiesBtn');
    if (rejectBtn) {
        rejectBtn.addEventListener('click', function() {
            rejectNonEssentialCookies();
            hideCookieBanner();
        });
    }
    
    // Botón para personalizar cookies
    const customizeBtn = document.getElementById('customizeCookiesBtn');
    if (customizeBtn) {
        customizeBtn.addEventListener('click', function() {
            window.location.href = '/cookie-settings';
        });
    }
}

function acceptAllCookies() {
    const settings = {
        preference_cookies: true,
        analytics_cookies: true,
        functional_cookies: true,
        third_party_cookies: true,
        anonymous_data: true,
        same_site_cookies: true,
        data_retention: '730',
        performance_cookies: true
    };
    
    saveCookieSettings(settings, 'all');
    showToast('🍪 Todas las cookies han sido aceptadas', 'success');
}

function rejectNonEssentialCookies() {
    const settings = {
        preference_cookies: false,
        analytics_cookies: false,
        functional_cookies: false,
        third_party_cookies: false,
        anonymous_data: false,
        same_site_cookies: true,
        data_retention: '30',
        performance_cookies: false
    };
    
    saveCookieSettings(settings, 'essential');
    showToast('🍪 Solo cookies esenciales activadas', 'info');
}

function saveCookieSettings(settings, consentType = 'custom') {
    // Guardar en localStorage
    localStorage.setItem('cookie_consent_given', 'true');
    localStorage.setItem('cookie_consent_date', new Date().toISOString());
    localStorage.setItem('cookie_settings', JSON.stringify(settings));
    
    // Enviar al servidor
    fetch('/save-cookie-settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Configuración guardada:', data);
            
            // Registrar consentimiento
            recordConsent(consentType);
            
            // Aplicar configuración
            applyCookieSettings();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error al guardar configuración', 'error');
    });
}

function recordConsent(consentType) {
    fetch('/api/cookies/consent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type: consentType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Consentimiento registrado:', data);
        }
    });
}

function applyCookieSettings() {
    const settings = getCookieSettings();
    
    // Configurar Google Analytics si está habilitado
    if (settings.analytics_cookies) {
        initAnalytics();
    }
    
    // Configurar cookies de funcionalidad
    if (settings.functional_cookies) {
        setupFunctionalCookies();
    }
    
    // Configurar cookies de rendimiento
    if (settings.performance_cookies) {
        setupPerformanceCookies();
    }
}

function getCookieSettings() {
    const saved = localStorage.getItem('cookie_settings');
    if (saved) {
        return JSON.parse(saved);
    }
    
    // Configuración por defecto
    return {
        preference_cookies: true,
        analytics_cookies: true,
        functional_cookies: true,
        third_party_cookies: false,
        anonymous_data: true,
        same_site_cookies: true,
        data_retention: '730',
        performance_cookies: true
    };
}

function initCookieSettings() {
    const form = document.getElementById('cookieSettingsForm');
    if (!form) return;
    
    // Botón para aceptar todo
    const acceptAllBtn = document.getElementById('acceptAllBtn');
    if (acceptAllBtn) {
        acceptAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            acceptAllCookies();
            showToast('Configuración aplicada', 'success');
            setTimeout(() => window.location.reload(), 1000);
        });
    }
    
    // Botón para rechazar todo
    const rejectAllBtn = document.getElementById('rejectAllBtn');
    if (rejectAllBtn) {
        rejectAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            rejectNonEssentialCookies();
            showToast('Configuración aplicada', 'info');
            setTimeout(() => window.location.reload(), 1000);
        });
    }
    
    // Botón para limpiar cookies
    const clearCookiesBtn = document.getElementById('clearCookiesBtn');
    if (clearCookiesBtn) {
        clearCookiesBtn.addEventListener('click', function() {
            if (confirm('¿Estás seguro de que quieres eliminar todas las cookies? Esto cerrará tu sesión.')) {
                clearAllCookies();
            }
        });
    }
    
    // Botón para exportar configuración
    const exportBtn = document.getElementById('exportSettingsBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            exportCookieSettings();
        });
    }
    
    // Enviar formulario
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const settings = {
            preference_cookies: formData.get('preference_cookies') === 'on',
            analytics_cookies: formData.get('analytics_cookies') === 'on',
            functional_cookies: formData.get('functional_cookies') === 'on',
            third_party_cookies: formData.get('third_party_cookies') === 'on',
            anonymous_data: formData.get('anonymous_data') === 'on',
            same_site_cookies: formData.get('same_site_cookies') === 'on',
            data_retention: formData.get('data_retention'),
            performance_cookies: formData.get('performance_cookies') === 'on'
        };
        
        saveCookieSettings(settings, 'custom');
        showToast('Configuración guardada', 'success');
        
        // Recargar después de guardar
        setTimeout(() => {
            window.location.reload();
        }, 1500);
    });
}

function clearAllCookies() {
    // Eliminar cookies del navegador
    document.cookie.split(";").forEach(function(c) {
        document.cookie = c.replace(/^ +/, "")
            .replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
    });
    
    // Limpiar localStorage
    localStorage.clear();
    
    // Limpiar sessionStorage
    sessionStorage.clear();
    
    // Enviar al servidor
    fetch('/api/cookies/clear', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Cookies eliminadas. Redirigiendo...', 'info');
            setTimeout(() => {
                window.location.href = '/logout';
            }, 2000);
        }
    });
}

function exportCookieSettings() {
    const settings = getCookieSettings();
    const dataStr = JSON.stringify(settings, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'cookie-settings-' + new Date().toISOString().split('T')[0] + '.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    showToast('Configuración exportada', 'success');
}

function setupTechnicalCookies() {
    // Cookie para evitar CSRF
    const csrfToken = generateCSRFToken();
    document.cookie = `csrf_token=${csrfToken}; SameSite=Strict; Path=/; Secure`;
    
    // Cookie para protección contra XSS
    document.cookie = 'XSS_Protection=1; HttpOnly; SameSite=Strict; Path=/; Secure';
}

function generateCSRFToken() {
    // Generar token CSRF aleatorio
    const array = new Uint8Array(32);
    window.crypto.getRandomValues(array);
    return Array.from(array, dec => ('0' + dec.toString(16)).substr(-2)).join('');
}

function initAnalytics() {
    // Inicializar Google Analytics (ejemplo)
    if (typeof gtag !== 'undefined') {
        gtag('consent', 'update', {
            'analytics_storage': 'granted'
        });
    }
    
    // Métricas personalizadas
    trackPageView();
    trackUserBehavior();
}

function trackPageView() {
    // Enviar métrica de página vista
    const pageData = {
        page: window.location.pathname,
        referrer: document.referrer,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent
    };
    
    // Enviar al endpoint de métricas
    fetch('/api/metrics/pageview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(pageData)
    });
}

function trackUserBehavior() {
    // Track clicks en elementos importantes
    document.addEventListener('click', function(e) {
        const target = e.target;
        
        // Solo trackear elementos con data-track attribute
        if (target.hasAttribute('data-track')) {
            const eventData = {
                event: 'click',
                element: target.getAttribute('data-track'),
                timestamp: new Date().toISOString(),
                page: window.location.pathname
            };
            
            fetch('/api/metrics/event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(eventData)
            });
        }
    });
}

function setupFunctionalCookies() {
    // Guardar preferencias de UI
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
    
    // Configurar recordatorios
    const reminders = JSON.parse(localStorage.getItem('reminders') || '[]');
    setupReminders(reminders);
}

function setupPerformanceCookies() {
    // Pre-cargar recursos importantes
    preloadImportantResources();
    
    // Cachear datos frecuentes
    setupDataCaching();
}

function preloadImportantResources() {
    const resources = [
        '/static/css/style.css',
        '/static/js/app.js'
    ];
    
    resources.forEach(resource => {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = resource;
        link.as = resource.endsWith('.css') ? 'style' : 'script';
        document.head.appendChild(link);
    });
}

function setupDataCaching() {
    // Cachear hábitos del usuario
    if ('caches' in window) {
        caches.open('habits-cache').then(cache => {
            cache.add('/api/habits');
        });
    }
}

function showToast(message, type = 'info') {
    // Implementación simple de toast
    const toast = document.createElement('div');
    toast.className = `cookie-toast cookie-toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Añadir estilos CSS para animaciones
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .cookie-banner {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: rgba(26, 27, 46, 0.95);
        backdrop-filter: blur(10px);
        border-top: 1px solid var(--border-color);
        padding: 1rem;
        z-index: 10000;
        opacity: 0;
        transform: translateY(100%);
        transition: all 0.3s ease;
    }
    
    .cookie-banner-content {
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    .cookie-banner-text {
        flex: 1;
        padding-right: 1rem;
    }
    
    @media (max-width: 768px) {
        .cookie-banner-content {
            flex-direction: column;
            text-align: center;
        }
        
        .cookie-banner-text {
            padding-right: 0;
            margin-bottom: 1rem;
        }
        
        .cookie-banner-buttons {
            display: flex;
            gap: 0.5rem;
        }
    }
`;
document.head.appendChild(style);