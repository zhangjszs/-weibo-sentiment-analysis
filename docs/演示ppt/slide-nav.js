/* ========================================================================
   Shared Presentation Navigation
   Handles keyboard arrow keys, prev/next buttons, and progress dots.
   All slides reference this single script.
   ======================================================================== */

class SlideNavigation {
    constructor(config = {}) {
        Object.assign(this, {
            prevSlideURL: null,
            nextSlideURL: null,
            totalSlides: 11,
            currentPage: 0,
            onChartInit: null
        }, config);

        this.init();
    }

    init() {
        this.bindKeyboard();
        this.bindButtons();
        this.renderProgressDots();
        if (this.onChartInit) this.onChartInit();
    }

    bindKeyboard() {
        document.addEventListener('keydown', (event) => {
            if (event.key === 'ArrowLeft' || event.keyCode === 37) {
                event.preventDefault();
                this.navigateTo(this.prevSlideURL);
            } else if (event.key === 'ArrowRight' || event.keyCode === 39) {
                event.preventDefault();
                this.navigateTo(this.nextSlideURL);
            }
        });
    }

    bindButtons() {
        const prevButton = document.querySelector('.prev-button');
        const nextButton = document.querySelector('.next-button');

        if (prevButton) {
            if (this.prevSlideURL) {
                prevButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.navigateTo(this.prevSlideURL);
                });
            } else {
                prevButton.classList.add('disabled');
                prevButton.href = '#';
            }
        }

        if (nextButton) {
            if (this.nextSlideURL) {
                nextButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.navigateTo(this.nextSlideURL);
                });
                nextButton.classList.remove('disabled');
                nextButton.href = this.nextSlideURL;
            } else {
                nextButton.classList.add('disabled');
                nextButton.href = '#';
            }
        }
    }

    navigateTo(url) {
        if (url) {
            window.location.href = url;
        }
    }

    renderProgressDots() {
        let progressContainer = document.querySelector('.slide-progress');
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'slide-progress';
            document.body.appendChild(progressContainer);
        }

        progressContainer.innerHTML = '';

        for (let i = 1; i <= this.totalSlides; i++) {
            const dot = document.createElement('div');
            dot.className = 'slide-progress-dot';
            if (i === this.currentPage) {
                dot.classList.add('active');
            }
            dot.addEventListener('click', () => {
                if (i !== this.currentPage) {
                    const pageMap = [
                        'index.html', 'ppt.html', '2.html', '3.html', '4.html',
                        '5.html', '6.html', '7.html', '8.html', '9.html', '10.html'
                    ];
                    const target = pageMap[i - 1];
                    if (target) window.location.href = target;
                }
            });
            progressContainer.appendChild(dot);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.slideNav = new SlideNavigation(window.SLIDE_CONFIG || {});
});
