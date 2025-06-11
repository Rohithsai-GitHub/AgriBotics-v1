document.addEventListener('DOMContentLoaded', function() {
    const weatherForm = document.getElementById('weatherForm');
    const weatherInfo = document.getElementById('weatherInfo');
    const forecastContainer = document.getElementById('forecastContainer');

    if (weatherForm) {
        weatherForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const city = document.getElementById('city').value;

            try {
                const response = await fetch(`/api/weather/forecast?city=${encodeURIComponent(city)}`);
                const data = await response.json();

                if (data.success) {
                    // Clear previous forecast
                    forecastContainer.innerHTML = '';

                    // Create forecast cards
                    data.forecast.forEach(day => {
                        const forecastCard = `
                            <div class="col-md-4 mb-3">
                                <div class="card">
                                    <div class="card-body">
                                        <div class="d-flex align-items-center mb-2">
                                            <img src="${day.icon}" alt="Weather icon" style="width: 64px; height: 64px;">
                                            <h6 class="mb-0 ms-2">${day.date}</h6>
                                        </div>
                                        <p class="mb-1">${day.description}</p>
                                        <p class="mb-1">Temperature: ${day.temperature.min}°C - ${day.temperature.max}°C</p>
                                        <p class="mb-1">Humidity: ${day.humidity}%</p>
                                        <p class="mb-0">Rainfall: ${day.rainfall}mm</p>
                                    </div>
                                </div>
                            </div>
                        `;
                        forecastContainer.innerHTML += forecastCard;
                    });

                    // Show weather info
                    weatherInfo.classList.remove('d-none');
                } else {
                    alert('Error fetching weather data: ' + data.error);
                }
            } catch (error) {
                console.error('Weather data error:', error);
                alert('Error fetching weather data. Please try again.');
            }
        });
    }
});