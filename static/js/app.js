// static/js/app.js - Lógica futurista mejorada

document.addEventListener('DOMContentLoaded', function() {
    // Efectos de animación al cargar
    animateElements();
    
    // Efectos de hover para cards
    initCardEffects();
    
    // Confirmaciones mejoradas para eliminación
    initDeleteConfirmations();
    
    // Efectos de formulario
    initFormEffects();
    
    // Contador de hábitos
    updateHabitStats();
});

function animateElements() {
    // Animación escalonada para los elementos
    const elements = document.querySelectorAll('.card, .list-group-item');
    elements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            element.style.transition = 'all 0.6s ease-out';
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

function initCardEffects() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

function initDeleteConfirmations() {
    const deleteForms = document.querySelectorAll('form[onsubmit*="confirm"]');
    
    deleteForms.forEach(form => {
        form.onsubmit = function(e) {
            e.preventDefault();
            
            // Crear modal de confirmación personalizado
            showCustomConfirm(
                '¿Eliminar hábito?',
                'Esta acción no se puede deshacer. ¿Estás seguro?',
                'Eliminar',
                'Cancelar'
            ).then(confirmed => {
                if (confirmed) {
                    form.submit();
                }
            });
        };
    });
}

function showCustomConfirm(title, message, confirmText, cancelText) {
    return new Promise((resolve) => {
        // Crear overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(15, 15, 26, 0.8);
            backdrop-filter: blur(5px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        
        // Crear modal
        const modal = document.createElement('div');
        modal.style.cssText = `
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: fadeIn 0.3s ease-out;
        `;
        
        modal.innerHTML = `
            <h4 style="color: var(--text-primary); margin-bottom: 1rem;">${title}</h4>
            <p style="color: var(--text-secondary); margin-bottom: 2rem;">${message}</p>
            <div style="display: flex; gap: 1rem; justify-content: flex-end;">
                <button class="btn btn-secondary" id="cancelBtn">${cancelText}</button>
                <button class="btn btn-danger" id="confirmBtn">${confirmText}</button>
            </div>
        `;
        
        overlay.appendChild(modal);
        document.body.appendChild(overlay);
        
        // Manejar eventos
        document.getElementById('cancelBtn').onclick = () => {
            document.body.removeChild(overlay);
            resolve(false);
        };
        
        document.getElementById('confirmBtn').onclick = () => {
            document.body.removeChild(overlay);
            resolve(true);
        };
        
        // Cerrar al hacer clic fuera
        overlay.onclick = (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
                resolve(false);
            }
        };
    });
}

function initFormEffects() {
    const inputs = document.querySelectorAll('.form-control');
    
    inputs.forEach(input => {
        // Efecto al enfocar
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Efecto de escritura
        input.addEventListener('input', function() {
            if (this.value) {
                this.style.background = 'rgba(45, 55, 72, 0.8)';
            } else {
                this.style.background = 'rgba(45, 55, 72, 0.5)';
            }
        });
    });
}

function updateHabitStats() {
    // Actualizar estadísticas en tiempo real
    const habitCount = document.querySelectorAll('.list-group-item').length;
    const today = new Date().toISOString().split('T')[0];
    
    const completedToday = Array.from(document.querySelectorAll('.list-group-item'))
        .filter(item => {
            const completedDates = item.querySelector('.completed-dates');
            return completedDates && completedDates.textContent.includes(today);
        }).length;
    
    // Actualizar contadores si existen
    const totalHabitsElement = document.querySelector('.total-habits');
    const completedTodayElement = document.querySelector('.completed-today');
    
    if (totalHabitsElement) {
        totalHabitsElement.textContent = habitCount;
    }
    
    if (completedTodayElement) {
        completedTodayElement.textContent = completedToday;
    }
}

// Efectos de partículas para el fondo (opcional)
function initParticles() {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    `;
    document.body.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    function createParticles() {
        particles = [];
        const particleCount = Math.min(50, Math.floor(window.innerWidth / 30));
        
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                size: Math.random() * 2 + 1,
                speedX: (Math.random() - 0.5) * 0.5,
                speedY: (Math.random() - 0.5) * 0.5,
                color: `rgba(99, 102, 241, ${Math.random() * 0.3 + 0.1})`
            });
        }
    }
    
    function animateParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach(particle => {
            particle.x += particle.speedX;
            particle.y += particle.speedY;
            
            // Rebotar en los bordes
            if (particle.x < 0 || particle.x > canvas.width) particle.speedX *= -1;
            if (particle.y < 0 || particle.y > canvas.height) particle.speedY *= -1;
            
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
            ctx.fillStyle = particle.color;
            ctx.fill();
        });
        
        requestAnimationFrame(animateParticles);
    }
    
    resizeCanvas();
    createParticles();
    animateParticles();
    
    window.addEventListener('resize', () => {
        resizeCanvas();
        createParticles();
    });
}

// Inicializar partículas (descomenta si quieres este efecto)
// initParticles();

// Notificaciones toast personalizadas
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-left: 4px solid ${type === 'success' ? 'var(--success-color)' : type === 'error' ? 'var(--danger-color)' : 'var(--primary-color)'};
        border-radius: 12px;
        color: var(--text-primary);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        transform: translateX(400px);
        transition: all 0.3s ease;
        max-width: 300px;
    `;
    
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        toast.style.transform = 'translateX(400px)';
        setTimeout(() => {
            document.body.removeChild(toast);
        }, 300);
    }, 3000);
}
// Manejar el completado de hábitos con feedback visual
function initHabitCompletion() {
    const completeForms = document.querySelectorAll('form[action*="/complete_habit/"]');
    
    completeForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Feedback visual inmediato
            submitBtn.innerHTML = '⏳ Completando...';
            submitBtn.disabled = true;
            submitBtn.classList.add('btn-secondary');
            submitBtn.classList.remove('btn-success');
            
            // Enviar el formulario después de un breve delay para que se vea el feedback
            setTimeout(() => {
                this.submit();
            }, 500);
        });
    });
}

// Actualizar estadísticas en tiempo real
function updateHabitStats() {
    const today = new Date().toISOString().split('T')[0];
    const habitItems = document.querySelectorAll('.list-group-item');
    let completedToday = 0;
    
    habitItems.forEach(item => {
        if (item.classList.contains('habit-completed')) {
            completedToday++;
        }
    });
    
    // Actualizar contadores en la UI
    const completedElement = document.querySelector('.completed-today');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress + small');
    
    if (completedElement) {
        completedElement.textContent = completedToday;
    }
    
    if (progressBar && progressText) {
        const totalHabits = habitItems.length;
        const percentage = totalHabits > 0 ? (completedToday / totalHabits * 100) : 0;
        
        progressBar.style.width = `${percentage}%`;
        progressText.textContent = 
            `${completedToday} de ${totalHabits} hábitos completados hoy (${percentage.toFixed(1)}%)`;
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initHabitCompletion();
    updateHabitStats();
    
    // Actualizar estadísticas cada 5 segundos (opcional)
    setInterval(updateHabitStats, 5000);
});

// Inicializar círculos de progreso
function initProgressCircles() {
    const progressCircles = document.querySelectorAll('.progress-circle');
    
    progressCircles.forEach(circle => {
        const percentage = circle.getAttribute('data-percentage');
        const progressBar = circle.querySelector('.progress-circle-bar');
        
        if (progressBar && percentage) {
            const circumference = 2 * Math.PI * 54;
            const offset = circumference - (percentage / 100) * circumference;
            
            // Aplicar la animación después de un pequeño delay
            setTimeout(() => {
                progressBar.style.strokeDashoffset = offset;
            }, 300);
        }
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    initProgressCircles();
    
    // Re-inicializar cuando se agreguen nuevos hábitos (para Single Page Apps)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initProgressCircles();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});