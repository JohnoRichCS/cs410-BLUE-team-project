document.addEventListener('DOMContentLoaded', () => {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }
});
// FAÍCT Action Plan Checklist
document.addEventListener('DOMContentLoaded', () => {
    const checklist = document.getElementById('action-checklist');
    const saveButton = document.getElementById('save-action-plan');
    const progress = document.getElementById('action-progress');
    const saveStatus = document.getElementById('action-save-status');

    // Only run on pages containing the checklist.
    if (!checklist || !saveButton || !progress || !saveStatus) {
        return;
    }

    const checkboxes = Array.from(
        checklist.querySelectorAll('.action-checkbox')
    );

    // Create a separate saved checklist for each claim.
    const claim = document.querySelector(
        '.bg-slate-100.italic'
    )?.textContent.trim() || '';

    const storageKey = 'faict-action-plan-' + claim;

    function updateProgress() {
        const completed = checkboxes.filter(
            checkbox => checkbox.checked
        ).length;

        progress.textContent =
            `${completed} of ${checkboxes.length} steps completed`;
    }

    // Restore the student's previously saved progress.
    try {
        const saved = JSON.parse(
            localStorage.getItem(storageKey) || '[]'
        );

        if (Array.isArray(saved)) {
            checkboxes.forEach((checkbox, index) => {
                checkbox.checked = saved[index] === true;
            });
        }
    } catch (error) {
        console.warn('Unable to load saved checklist.');
    }

    updateProgress();

    // Update the progress whenever a checkbox changes.
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            updateProgress();
            saveStatus.textContent = 'Unsaved changes';
        });
    });

    // Save progress when the student clicks the button.
    saveButton.addEventListener('click', () => {
        const checkedSteps = checkboxes.map(
            checkbox => checkbox.checked
        );

        try {
            localStorage.setItem(
                storageKey,
                JSON.stringify(checkedSteps)
            );

            saveStatus.textContent = 'Checklist saved successfully!';
        } catch (error) {
            saveStatus.textContent =
                'Unable to save checklist in this browser.';
        }
    });
});
// FAÍCT Student Feedback
document.addEventListener('DOMContentLoaded', () => {
    const yesButton = document.getElementById('feedback-yes');
    const noButton = document.getElementById('feedback-no');
    const feedbackStatus = document.getElementById('feedback-status');

    // Only run on pages containing the feedback buttons.
    if (!yesButton || !noButton || !feedbackStatus) {
        return;
    }

    // Keep feedback separate for each claim.
    const claim = document.querySelector(
        '.bg-slate-100.italic'
    )?.textContent.trim() || '';

    const feedbackKey = 'faict-feedback-' + claim;

    function showFeedback(choice) {
        feedbackStatus.textContent =
            `Thank you! Your "${choice}" feedback was saved in this browser.`;
    }

    function saveFeedback(choice) {
        try {
            localStorage.setItem(feedbackKey, choice);
            showFeedback(choice);
        } catch (error) {
            feedbackStatus.textContent =
                'Unable to save feedback in this browser.';
        }
    }

    // Restore previously saved feedback.
    try {
        const savedFeedback = localStorage.getItem(feedbackKey);

        if (savedFeedback === 'Yes' || savedFeedback === 'No') {
            showFeedback(savedFeedback);
        }
    } catch (error) {
        console.warn('Unable to load saved feedback.');
    }

    yesButton.addEventListener('click', () => {
        saveFeedback('Yes');
    });

    noButton.addEventListener('click', () => {
        saveFeedback('No');
    });
});