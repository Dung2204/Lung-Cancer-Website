document.addEventListener('DOMContentLoaded', function() {
    // Client-side validation for Register Form
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const password = document.getElementById('password').value;
            const confirmPassword = document.getElementById('confirm_password').value;
            let isValid = true;

            // Simple password length validation
            if (password.length < 6) {
                alert('Mật khẩu phải có ít nhất 6 ký tự.');
                isValid = false;
            }
            // Password match validation
            if (password !== confirmPassword) {
                alert('Mật khẩu xác nhận không khớp.');
                isValid = false;
            }

            if (!isValid) {
                event.preventDefault(); // Stop form submission
            } else {
                // Show loading state for button
                const submitButton = registerForm.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang đăng ký...';
                }
            }
        });
    }

    // Client-side validation for Diagnose Form
    const diagnoseForm = document.getElementById('diagnose-form');
    if (diagnoseForm) {
        diagnoseForm.addEventListener('submit', function(event) {
            const ageInput = document.getElementById('age');
            const age = parseInt(ageInput.value);
            let isValid = true;

            if (isNaN(age) || age <= 0 || age > 120) {
                alert('Vui lòng nhập tuổi hợp lệ (một số dương từ 1 đến 120).');
                isValid = false;
            }

            // You can add more client-side validation for other fields if needed

            if (!isValid) {
                event.preventDefault(); // Stop form submission
            } else {
                // Show loading state for button
                const submitButton = diagnoseForm.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang chẩn đoán...';
                }
            }
        });
    }

    // General loading state for other submit buttons if they exist
    // This targets any form that doesn't have a specific ID handled above
    document.querySelectorAll('form:not(#register-form):not(#diagnose-form)').forEach(form => {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                // Preserve original text and add spinner
                submitButton.dataset.originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang xử lý...';
            }
        });
    });
});

// static/js/script.js

window.addEventListener("DOMContentLoaded", () => {
    console.log("✅ JS script đã load xong!");

    // ... (các phần code xử lý form đăng nhập, đăng ký, chẩn đoán hiện có) ...

    // Xử lý chuyển đổi tab trên trang hồ sơ
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabContents = document.querySelectorAll(".tab-content");

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            // Loại bỏ 'active' từ tất cả các nút và nội dung tab
            tabButtons.forEach(btn => btn.classList.remove("active"));
            tabContents.forEach(content => content.classList.remove("active"));

            // Thêm 'active' cho nút được click
            button.classList.add("active");

            // Hiển thị nội dung tab tương ứng
            const tabId = button.dataset.tab;
            document.getElementById(`${tabId}-tab-content`).classList.add("active");
        });
    });

    // Hàm xem trước ảnh đại diện
    window.previewAvatar = function(event) {
        const reader = new FileReader();
        reader.onload = function() {
            const output = document.getElementById('current-avatar-img');
            output.src = reader.result;
        };
        reader.readAsDataURL(event.target.files[0]);
    };

}); // Kết thúc DOMContentLoaded