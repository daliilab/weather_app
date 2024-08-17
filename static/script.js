document.addEventListener('DOMContentLoaded', () => {
    const box = document.querySelector('.box');
  
    box.addEventListener('mouseover', () => {
      box.style.transform = 'scale(1.2)';
      box.style.backgroundColor = '#60349a';
    });
  
    box.addEventListener('mouseout', () => {
      box.style.transform = 'scale(1)';
      box.style.backgroundColor = '#3498db';
    });
  }); 

