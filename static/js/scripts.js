// scripts.js

// Function to update cart count in the navbar
function updateCartCount() {
    fetch('/cart/count/')  // Assumes a view exists to return cart count
        .then(response => response.json())
        .then(data => {
            document.querySelector('.nav-link[href="/cart/"]').textContent = `Cart (${data.count})`;
        })
        .catch(error => console.error('Error fetching cart count:', error));
}

// Call updateCartCount on page load
document.addEventListener('DOMContentLoaded', updateCartCount);



// Handle add to cart form submission
document.querySelectorAll('form[action^="/add_to_cart/"]').forEach(form => {
    form.addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = new FormData(this);
        fetch(this.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': formData.get('csrfmiddlewaretoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateCartCount();
                alert('Added to cart!');
            } else {
                alert('Error adding to cart.');
            }
        })
        .catch(error => console.error('Error adding to cart:', error));
    });
});

// QR Code Scanner (using a library like jsQR or ZXing)
function startQRScanner() {
    const video = document.createElement('video');
    const canvasElement = document.getElementById('qr-reader');
    const canvas = canvasElement.getContext('2d');

    navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
        .then(stream => {
            video.srcObject = stream;
            video.setAttribute('playsinline', true);
            video.play();
            requestAnimationFrame(tick);
        })
        .catch(error => console.error('Error accessing camera:', error));

    function tick() {
        if (video.readyState === video.HAVE_ENOUGH_DATA) {
            canvasElement.height = video.videoHeight;
            canvasElement.width = video.videoWidth;
            canvas.drawImage(video, 0, 0, canvasElement.width, canvasElement.height);
            const imageData = canvas.getImageData(0, 0, canvasElement.width, canvasElement.height);
            const code = jsQR(imageData.data, imageData.width, imageData.height);
            if (code) {
                // Handle the scanned QR code
                console.log('QR Code detected:', code.data);
                // Send code to server for verification
                fetch('/verify_ticket/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': '{{ csrf_token }}'
                    },
                    body: JSON.stringify({ code: code.data })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Invalid or expired ticket.');
                    } else {
                        alert('Invalid or expired ticket.');
                    }
                })
                .catch(error => console.error('Error verifying ticket:', error));
            }
        }
        requestAnimationFrame(tick);
    }
}

// Start QR scanner when on verification page
if (window.location.pathname === '/verify_ticket/') {
    startQRScanner();
}