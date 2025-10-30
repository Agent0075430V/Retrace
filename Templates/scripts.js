// Navbar active link
const links = document.querySelectorAll('nav ul li a');
links.forEach(link => {
    if(link.href === window.location.href){
        link.classList.add('active');
    }
});

// Image preview
function previewImage(input, previewId){
    const file = input.files[0];
    const preview = document.getElementById(previewId);
    if(file){
        const reader = new FileReader();
        reader.onload = function(e){
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
        reader.readAsDataURL(file);
    }
}
