/**
 * BreakfastWise - Registration Controller
 * Handles client-side validation, password toggles, API submission, and state feedback.
 */

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('register-form');
  const btnSubmit = document.getElementById('btn-register');
  const alertBox = document.getElementById('auth-alert');
  const alertMsg = document.getElementById('alert-message');
  const alertIcon = document.getElementById('alert-icon');

  // Input elements
  const fullNameInput = document.getElementById('full_name');
  const usernameInput = document.getElementById('username');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm_password');

  // Feedback elements
  const feedbackFullName = document.getElementById('feedback-full-name');
  const feedbackUsername = document.getElementById('feedback-username');
  const feedbackEmail = document.getElementById('feedback-email');
  const feedbackPassword = document.getElementById('feedback-password');
  const feedbackConfirm = document.getElementById('feedback-confirm-password');

  // Password visibility toggle helpers
  function setupPasswordToggle(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const input = document.getElementById(inputId);
    if (!btn || !input) return;

    const eyeOpen = btn.querySelector('.eye-open');
    const eyeClosed = btn.querySelector('.eye-closed');

    btn.addEventListener('click', () => {
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      
      if (eyeOpen && eyeClosed) {
        eyeOpen.style.display = isPassword ? 'none' : 'block';
        eyeClosed.style.display = isPassword ? 'block' : 'none';
      }

      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      btn.setAttribute('title', isPassword ? 'Hide password' : 'Show password');
      input.focus();
    });
  }

  setupPasswordToggle('toggle-password', 'password');
  setupPasswordToggle('toggle-confirm-password', 'confirm_password');

  // Validation rules
  const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
  const usernameRegex = /^[a-zA-Z0-9_]{3,30}$/;

  function validateField(input, feedbackEl, isValid, message) {
    if (isValid) {
      input.classList.remove('is-invalid');
      if (feedbackEl) feedbackEl.classList.remove('visible');
      return true;
    } else {
      input.classList.add('is-invalid');
      if (feedbackEl) {
        if (message) feedbackEl.textContent = message;
        feedbackEl.classList.add('visible');
      }
      return false;
    }
  }

  // Real-time validation listeners
  fullNameInput.addEventListener('input', () => {
    const val = fullNameInput.value.trim();
    validateField(fullNameInput, feedbackFullName, val.length >= 2, 'Please enter your full name (at least 2 characters).');
  });

  usernameInput.addEventListener('input', () => {
    const val = usernameInput.value.trim();
    validateField(usernameInput, feedbackUsername, usernameRegex.test(val), 'Username must be 3-30 characters (letters, numbers, underscores).');
  });

  emailInput.addEventListener('input', () => {
    const val = emailInput.value.trim();
    validateField(emailInput, feedbackEmail, emailRegex.test(val), 'Please enter a valid email address.');
  });

  passwordInput.addEventListener('input', () => {
    const val = passwordInput.value;
    validateField(passwordInput, feedbackPassword, val.length >= 8, 'Password must be at least 8 characters long.');
    if (confirmPasswordInput.value) {
      validateField(
        confirmPasswordInput,
        feedbackConfirm,
        confirmPasswordInput.value === val,
        'Passwords must match.'
      );
    }
  });

  confirmPasswordInput.addEventListener('input', () => {
    const val = confirmPasswordInput.value;
    validateField(
      confirmPasswordInput,
      feedbackConfirm,
      val === passwordInput.value,
      'Passwords must match.'
    );
  });

  function showAlert(message, type = 'error') {
    if (!alertBox || !alertMsg) return;
    alertMsg.textContent = message;
    alertIcon.textContent = type === 'success' ? '✓' : '⚠️';
    alertBox.className = `auth-alert ${type}`;
    alertBox.style.display = 'flex';
  }

  function hideAlert() {
    if (alertBox) {
      alertBox.style.display = 'none';
    }
  }

  // Form submission handler
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideAlert();

    const fullName = fullNameInput.value.trim();
    const username = usernameInput.value.trim();
    const email = emailInput.value.trim().toLowerCase();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    // Validate all fields
    const isNameValid = validateField(fullNameInput, feedbackFullName, fullName.length >= 2);
    const isUserValid = validateField(usernameInput, feedbackUsername, usernameRegex.test(username));
    const isEmailValid = validateField(emailInput, feedbackEmail, emailRegex.test(email));
    const isPassValid = validateField(passwordInput, feedbackPassword, password.length >= 8);
    const isConfirmValid = validateField(confirmPasswordInput, feedbackConfirm, password === confirmPassword);

    if (!isNameValid || !isUserValid || !isEmailValid || !isPassValid || !isConfirmValid) {
      showAlert('Please correct the highlighted errors before submitting.', 'error');
      // Focus first invalid input
      const firstInvalid = form.querySelector('.form-input.is-invalid');
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    // Enter loading state
    btnSubmit.disabled = true;
    btnSubmit.classList.add('loading');
    const originalBtnText = btnSubmit.querySelector('.btn-text').textContent;
    btnSubmit.querySelector('.btn-text').textContent = 'Creating Account...';

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          full_name: fullName,
          username: username,
          email: email,
          password: password,
          confirm_password: confirmPassword,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        let errorDetail = data.detail;
        if (Array.isArray(errorDetail)) {
          errorDetail = errorDetail.join(' ');
        }
        throw new Error(errorDetail || 'Registration failed. Please try again.');
      }

      // Successful Registration
      showAlert(`✓ Account successfully created for ${data.full_name}! Redirecting to dashboard...`, 'success');
      form.reset();

      // Clear any validation states
      form.querySelectorAll('.form-input').forEach(inp => inp.classList.remove('is-invalid'));
      form.querySelectorAll('.form-feedback').forEach(fb => fb.classList.remove('visible'));

      // Redirect to main application dashboard after 2 seconds
      setTimeout(() => {
        window.location.href = '/';
      }, 2000);

    } catch (err) {
      showAlert(err.message || 'An unexpected error occurred. Please try again.', 'error');
      btnSubmit.disabled = false;
      btnSubmit.classList.remove('loading');
      btnSubmit.querySelector('.btn-text').textContent = originalBtnText;
    }
  });
});
