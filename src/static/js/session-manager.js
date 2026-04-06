/**
 * 会话管理工具
 * 微博舆情分析可视化系统
 * 功能：检测会话状态、自动跳转、错误处理
 */

class SessionManager {
    constructor() {
        this.checkInterval = 60000; // 每分钟检查一次会话状态
        this.warningTime = 300000; // 会话过期前5分钟警告
        this.sessionTimeout = 3600000; // 1小时会话超时（与后端配置一致）
        this.lastActivityTime = Date.now();
        this.warningShown = false;

        this.init();
    }

    /**
     * 初始化会话管理器
     */
    init() {
        // 监听用户活动
        this.bindActivityListeners();

        // 定期检查会话状态
        this.startSessionCheck();

        // 监听页面可见性变化
        this.bindVisibilityListener();

        console.log('会话管理器已初始化');
    }

    /**
     * 绑定用户活动监听器
     */
    bindActivityListeners() {
        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, () => {
                this.updateLastActivity();
            }, true);
        });
    }

    /**
     * 更新最后活动时间
     */
    updateLastActivity() {
        this.lastActivityTime = Date.now();
        this.warningShown = false;
    }

    /**
     * 开始会话状态检查
     */
    startSessionCheck() {
        setInterval(() => {
            this.checkSessionStatus();
        }, this.checkInterval);
    }

    /**
     * 检查会话状态
     */
    async checkSessionStatus() {
        try {
            const response = await fetch('/api/session/check', {
                method: 'GET',
                credentials: 'same-origin', // 确保发送cookies
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.status === 401) {
                // 会话已过期
                this.handleSessionExpired();
                return;
            }

            if (!response.ok) {
                console.warn('会话检查失败:', response.status);
                return;
            }

            const payload = await response.json();

            if (!payload?.data?.authenticated) {
                this.handleSessionExpired();
                return;
            }

            // 检查是否需要显示警告
            const timeLeft = this.sessionTimeout - (Date.now() - this.lastActivityTime);
            if (timeLeft <= this.warningTime && !this.warningShown) {
                this.showSessionWarning(Math.floor(timeLeft / 60000));
            }

        } catch (error) {
            console.error('会话检查错误:', error);
        }
    }

    /**
     * 显示会话即将过期警告
     */
    showSessionWarning(minutesLeft) {
        this.warningShown = true;

        if (typeof Swal !== 'undefined') {
            // 使用SweetAlert显示警告
            Swal.fire({
                title: '会话即将过期',
                text: `您的登录会话将在 ${minutesLeft} 分钟后过期，请及时保存数据。`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: '延长会话',
                cancelButtonText: '忽略',
                timer: 15000,
                timerProgressBar: true
            }).then((result) => {
                if (result.isConfirmed) {
                    this.extendSession();
                }
            });
        } else {
            // 备用警告方式
            const extend = confirm(`您的登录会话将在 ${minutesLeft} 分钟后过期，是否延长会话？`);
            if (extend) {
                this.extendSession();
            }
        }
    }

    /**
     * 延长会话
     */
    async extendSession() {
        try {
            const response = await fetch('/api/session/extend', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (response.ok) {
                this.updateLastActivity();
                this.showMessage('会话已延长', 'success');
            } else {
                this.showMessage('会话延长失败', 'error');
            }
        } catch (error) {
            console.error('延长会话失败:', error);
            this.showMessage('网络错误，无法延长会话', 'error');
        }
    }

    /**
     * 处理会话过期
     */
    handleSessionExpired() {
        console.log('会话已过期，准备跳转到登录页');

        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: '会话已过期',
                text: '您的登录会话已过期，请重新登录。',
                icon: 'info',
                confirmButtonText: '重新登录',
                allowOutsideClick: false,
                allowEscapeKey: false
            }).then(() => {
                this.redirectToLogin();
            });
        } else {
            alert('您的登录会话已过期，请重新登录。');
            this.redirectToLogin();
        }
    }

    /**
     * 跳转到登录页
     */
    redirectToLogin() {
        // 保存当前页面路径，登录后可以返回
        const currentPath = window.location.pathname + window.location.search;
        sessionStorage.setItem('redirectAfterLogin', currentPath);

        // 跳转到登录页
        window.location.href = '/user/login';
    }

    /**
     * 显示消息
     */
    showMessage(message, type = 'info') {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                text: message,
                icon: type,
                timer: 3000,
                showConfirmButton: false,
                toast: true,
                position: 'top-end'
            });
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    /**
     * 绑定页面可见性监听器
     */
    bindVisibilityListener() {
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                // 页面重新可见时检查会话状态
                this.checkSessionStatus();
            }
        });
    }

    /**
     * 手动检查会话（供其他模块调用）
     */
    manualCheck() {
        return this.checkSessionStatus();
    }
}

// 全局错误处理函数
function handleAjaxError(xhr, status, error) {
    if (xhr.status === 401) {
        // 未授权，可能是会话过期
        if (window.sessionManager) {
            window.sessionManager.handleSessionExpired();
        } else {
            window.location.href = '/user/login';
        }
        return true;
    }
    return false;
}

// 增强的fetch函数，自动处理会话过期
window.safeFetch = async function (url, options = {}) {
    try {
        // 确保包含凭据
        options.credentials = options.credentials || 'same-origin';

        const response = await fetch(url, options);

        if (response.status === 401) {
            if (window.sessionManager) {
                window.sessionManager.handleSessionExpired();
            } else {
                window.location.href = '/user/login';
            }
            throw new Error('Session expired');
        }

        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
};

// 页面加载时自动初始化会话管理器
document.addEventListener('DOMContentLoaded', function () {
    // 只在需要认证的页面初始化会话管理器
    const isAuthPage = !window.location.pathname.startsWith('/user/login') &&
        !window.location.pathname.startsWith('/user/register');

    if (isAuthPage) {
        window.sessionManager = new SessionManager();
    }

    // 检查是否有登录后需要重定向的路径
    const redirectPath = sessionStorage.getItem('redirectAfterLogin');
    if (redirectPath && window.location.pathname === '/page/home') {
        sessionStorage.removeItem('redirectAfterLogin');
        if (redirectPath !== '/page/home') {
            window.location.href = redirectPath;
        }
    }
});

// 为jQuery Ajax请求添加全局错误处理（如果使用了jQuery）
if (typeof $ !== 'undefined') {
    $(document).ajaxError(function (event, xhr, settings, error) {
        handleAjaxError(xhr, settings, error);
    });
}

// 导出全局函数供外部调用
window.SessionUtils = {
    checkSession: () => window.sessionManager?.manualCheck(),
    extendSession: () => window.sessionManager?.extendSession(),
    logout: async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
        } catch (error) {
            console.error('注销失败:', error);
        } finally {
            window.location.href = '/user/login';
        }
    }
};
