document.addEventListener('DOMContentLoaded', function() {
    const weatherForm = document.getElementById('weatherForm');
    const weatherInfo = document.getElementById('weatherInfo');
    const predictionForm = document.getElementById('predictionForm');
    const loadingSpinner = document.querySelector('.loading-spinner');
    const resultCard = document.querySelector('.result-card');
    const predictionResult = document.getElementById('predictionResult');

    // Weather form submission
    if (weatherForm) {
        weatherForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const city = document.getElementById('city').value;

            try {
                const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}`);
                const data = await response.json();

                if (data.success) {
                    // Update weather display
                    document.getElementById('weatherIcon').src = `http://openweathermap.org/img/w/${data.weather.icon}.png`;
                    document.getElementById('weatherDescription').textContent = data.weather.description;
                    document.getElementById('weatherTemp').textContent = data.weather.temperature;
                    document.getElementById('weatherHumidity').textContent = data.weather.humidity;
                    document.getElementById('weatherRainfall').textContent = data.weather.rainfall;

                    // Show weather info card
                    weatherInfo.classList.remove('d-none');

                    // Auto-fill prediction form with weather data
                    document.getElementById('temperature').value = data.weather.temperature;
                    document.getElementById('humidity').value = data.weather.humidity;
                    document.getElementById('rainfall').value = data.weather.rainfall;
                } else {
                    alert('Error fetching weather data: ' + data.error);
                }
            } catch (error) {
                console.error('Weather data error:', error);
                alert('Error fetching weather data. Please try again.');
            }
        });
    }

    // Prediction form submission
    if (predictionForm) {
        predictionForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            // Show loading spinner
            loadingSpinner.style.display = 'block';
            resultCard.style.display = 'none';

            const formData = {
                nitrogen: parseFloat(document.getElementById('nitrogen').value),
                phosphorus: parseFloat(document.getElementById('phosphorus').value),
                potassium: parseFloat(document.getElementById('potassium').value),
                temperature: parseFloat(document.getElementById('temperature').value),
                humidity: parseFloat(document.getElementById('humidity').value),
                ph: parseFloat(document.getElementById('ph').value),
                rainfall: parseFloat(document.getElementById('rainfall').value)
            };

            try {
                const response = await fetch('/api/predict', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    predictionResult.textContent = `Recommended crop: ${data.prediction}`;
                    resultCard.style.display = 'block';
                } else {
                    alert('Prediction failed: ' + data.error);
                }
            } catch (error) {
                console.error('Prediction error:', error);
                alert('An error occurred during prediction. Please try again.');
            } finally {
                loadingSpinner.style.display = 'none';
            }
        });
    }
});