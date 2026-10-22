
document.addEventListener('DOMContentLoaded', () => {
    // Mobile navigation
    const menu = document.querySelector('.menu');
    const nav = document.querySelector('nav');

    if (menu && nav) {
        menu.addEventListener('click', () => {
            const isOpen = nav.classList.toggle('open');

            menu.setAttribute('aria-expanded', String(isOpen));
            menu.setAttribute(
                'aria-label',
                isOpen ? 'Close navigation' : 'Open navigation'
            );
        });

        nav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                nav.classList.remove('open');
                menu.setAttribute('aria-expanded', 'false');
                menu.setAttribute('aria-label', 'Open navigation');
            });
        });
    }

    // Conditional project and technology fields
    const projectType = document.querySelector('#project_type');
    const technology = document.querySelector('#technology');

    const toggleConditionalFields = () => {
        const isOtherProject =
            projectType && projectType.value === 'other';

        const isOtherTechnology =
            technology &&
            technology.value === 'Other technology';

        document.querySelectorAll('.project-other').forEach(element => {
            element.classList.toggle('show', Boolean(isOtherProject));
        });

        document.querySelectorAll('.tech-other').forEach(element => {
            element.classList.toggle('show', Boolean(isOtherTechnology));
        });
    };

    projectType?.addEventListener('change', toggleConditionalFields);
    technology?.addEventListener('change', toggleConditionalFields);

    toggleConditionalFields();

    // Project portfolio filters
    const filterButtons = document.querySelectorAll('.filters button');
    const projects = document.querySelectorAll('.project');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const selectedFilter = button.dataset.filter || 'all';

            filterButtons.forEach(item => {
                item.classList.toggle('active', item === button);
            });

            projects.forEach(project => {
                const category = project.dataset.category;

                project.hidden =
                    selectedFilter !== 'all' &&
                    category !== selectedFilter;
            });
        });
    });

    // Contact form submission feedback
    const form = document.querySelector('form');

    form?.addEventListener('submit', event => {
        if (!form.checkValidity()) {
            return;
        }

        const submitButton = form.querySelector('.submit');

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Sending inquiry…';
        }
    });
});
