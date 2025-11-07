// Auto-dismiss success messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const successMessages = document.querySelectorAll('.message-success');

    successMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            message.style.transition = 'opacity 0.5s';

            setTimeout(function() {
                message.remove();
            }, 500);
        }, 5000);
    });
});
