window.addEventListener('DOMContentLoaded', () => {
    const hash = window.location.hash.substring(1);
    const params = new URLSearchParams(hash);
    const accessToken = params.get('access_token');
    if (accessToken) {
        document.getElementById('access_token').value = accessToken;
    }
});