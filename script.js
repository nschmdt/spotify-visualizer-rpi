// CONFIGURATION
const CANVAS_SIZE = 600;
const MATRIX_SIZE = 32;
const CLIENT_ID = 'b245d267eebd4c97a090419d44fbd396'; // Replace!
const LED_SHAPE = 'circle'; // 'circle' or 'square'
const LED_SPACING = CANVAS_SIZE / MATRIX_SIZE;
const LED_RADIUS = LED_SPACING / 2.3;


// PKCE helpers
function generateRandomString(length) {
    const possible = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const values = crypto.getRandomValues(new Uint8Array(length));
    return values.reduce((acc, x) => acc + possible[x % possible.length], "");
}

async function sha256(plain) {
    const encoder = new TextEncoder();
    const data = encoder.encode(plain);
    return window.crypto.subtle.digest('SHA-256', data);
}

function base64encode(input) {
    return btoa(String.fromCharCode(...new Uint8Array(input)))
        .replace(/=/g, '')
        .replace(/\+/g, '-')
        .replace(/\//g, '_');
}

async function loginWithSpotify() {
    const codeVerifier = generateRandomString(64);
    const hashed = await sha256(codeVerifier);
    const codeChallenge = base64encode(hashed);

    sessionStorage.setItem('code_verifier', codeVerifier);

    const authUrl = 'https://accounts.spotify.com/authorize?' +
        'client_id=' + CLIENT_ID +
        '&response_type=code' +
        '&redirect_uri=' + encodeURIComponent(window.location.origin) +
        '&scope=user-read-currently-playing' +
        '&code_challenge_method=S256' +
        '&code_challenge=' + codeChallenge;

    window.location.href = authUrl;
}

async function handleCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');

    if (code) {
        console.log('Found code, exchanging for token...');

        try {
            const response = await fetch('https://accounts.spotify.com/api/token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    client_id: CLIENT_ID,
                    grant_type: 'authorization_code',
                    code: code,
                    redirect_uri: window.location.origin,
                    code_verifier: sessionStorage.getItem('code_verifier'),
                })
            });

            const data = await response.json();
            console.log('Token response:', data);

            if (data.access_token) {
                sessionStorage.setItem('access_token', data.access_token);
                window.history.replaceState({}, document.title, '/');
                startVisualizer();
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
}

function startVisualizer() {
    document.getElementById('login-container').style.display = 'none';
    document.getElementById('visualizer').classList.add('active');

    const canvas = document.getElementById('led-matrix');
    canvas.width = CANVAS_SIZE;
    canvas.height = CANVAS_SIZE;

    checkCurrentTrack();
    setInterval(checkCurrentTrack, 1000);
}

async function checkCurrentTrack() {
    const token = sessionStorage.getItem('access_token');
    if (!token) return;

    try {
        const response = await fetch('https://api.spotify.com/v1/me/player/currently-playing', {
            headers: { 'Authorization': 'Bearer ' + token }
        });

        if (response.ok && response.status !== 204) {
            const data = await response.json();
            if (data && data.item && data.item.album.images[0]) {
                drawLEDMatrix(data.item.album.images[0].url);
            }
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function drawLEDMatrix(imageUrl) {
    const canvas = document.getElementById('led-matrix');
    const ctx = canvas.getContext('2d');

    const tempCanvas = document.createElement('canvas');
    const tempCtx = tempCanvas.getContext('2d');
    tempCanvas.width = MATRIX_SIZE;
    tempCanvas.height = MATRIX_SIZE;

    const img = new Image();
    img.crossOrigin = 'anonymous';

    img.onload = function () {
        ctx.fillStyle = '#000000';
        ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

        tempCtx.drawImage(img, 0, 0, MATRIX_SIZE, MATRIX_SIZE);
        const pixelData = tempCtx.getImageData(0, 0, MATRIX_SIZE, MATRIX_SIZE).data;

        for (let y = 0; y < MATRIX_SIZE; y++) {
            for (let x = 0; x < MATRIX_SIZE; x++) {
                const pixelIndex = (y * MATRIX_SIZE + x) * 4;
                const r = pixelData[pixelIndex];
                const g = pixelData[pixelIndex + 1];
                const b = pixelData[pixelIndex + 2];

                ctx.fillStyle = `rgb(${r},${g},${b})`;

                if (LED_SHAPE === 'circle') {
                    ctx.beginPath();
                    ctx.arc(
                        x * LED_SPACING + LED_SPACING / 2,
                        y * LED_SPACING + LED_SPACING / 2,
                        LED_RADIUS,
                        0,
                        Math.PI * 2
                    );
                    ctx.fill();
                } else if (LED_SHAPE === 'square') {
                    ctx.fillRect(
                        x * LED_SPACING + 1,
                        y * LED_SPACING + 1,
                        LED_SPACING - 2,
                        LED_SPACING - 2
                    );
                }
            }
        }
    };

    img.onerror = function () {
        console.log('Image failed to load');
    };

    img.src = imageUrl;
}

window.addEventListener('load', function () {
    createCustomCursor(); 
    handleCallback();
});


function goFullscreen() {
    if (document.documentElement.requestFullscreen) {
        document.documentElement.requestFullscreen();
    } else if (document.documentElement.webkitRequestFullscreen) {
        document.documentElement.webkitRequestFullscreen();
    }
}


let cursorTimeout;
let isFullscreen = false;
// Listen for fullscreen changes to show/hide button
document.addEventListener('fullscreenchange', function () {
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (document.fullscreenElement) {
        fullscreenBtn.style.display = 'none';
        isFullscreen = true;
        startCursorAutoHide();
    } else {
        fullscreenBtn.style.display = 'block';
        isFullscreen = false;
        showCursor();
    }
});

document.addEventListener('webkitfullscreenchange', function () {
    const fullscreenBtn = document.getElementById('fullscreen-btn');
    if (document.webkitFullscreenElement) {
        fullscreenBtn.style.display = 'none';
        isFullscreen = true;
        startCursorAutoHide();
    } else {
        fullscreenBtn.style.display = 'block';
        isFullscreen = false;
        showCursor();
    }
});

function startCursorAutoHide() {
    clearTimeout(cursorTimeout);
    cursorTimeout = setTimeout(hideCursor, 3000); // Hide after 3 seconds
}

function hideCursor() {
    if (isFullscreen) {
        const cursor = document.getElementById('custom-cursor');
        if (cursor) cursor.style.display = 'none';
    }
}

function showCursor() {
    const cursor = document.getElementById('custom-cursor');
    if (cursor) cursor.style.display = 'block';

    if (isFullscreen) {
        clearTimeout(cursorTimeout);
        cursorTimeout = setTimeout(hideCursor, 1000);
    }
}


document.addEventListener('mousemove', function (e) {
    let cursor = document.getElementById('custom-cursor');
    if (cursor) {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';

        if (isFullscreen) {
            showCursor();
        }
    }
});



function createCustomCursor() {
    let cursor = document.getElementById('custom-cursor');
    if (!cursor) {
        cursor = document.createElement('div');
        cursor.id = 'custom-cursor';
        cursor.style.cssText = `
            position: fixed;
            width: 40px;
            height: 40px;
            background: #ffee00ff;
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            transform: translate(-20px, -20px);
            //box-shadow: 0 0 10px #39ff14;
            display: block;
        `;
        document.body.appendChild(cursor);
    }
}