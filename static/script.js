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

/* <script>
    document.addEventListener("DOMContentLoaded", function() {
        var inputField = document.getElementById("city-input");
        var button = document.getElementById("location-btn");

        inputField.addEventListener("input", function() {
            var cityName = inputField.value.trim(); // Get the input value and trim any whitespace
            button.textContent = cityName ? cityName + ', BA' : 'Sarajevo, BA';
        });
    });
</script> */