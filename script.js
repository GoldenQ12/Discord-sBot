document.addEventListener("DOMContentLoaded", function() {
    fetch('cards.json')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(cards => {
            const cardGallery = document.getElementById('card-gallery');
            cards.forEach(card => {
                const cardElement = document.createElement('div');
                cardElement.className = 'card';
                
                // Set the background color based on card_color
                cardElement.style.background = getColor(card.card_color);
                
                cardElement.innerHTML = `
                    <img src="${card.card_url}" alt="${card.card_name}">
                    <h2>${card.card_name}</h2>
                    <p>Number: ${card.card_number}</p>
                    <p>Color: ${card.card_color}</p>
                    <p>Cost: ${card.cost}</p>
                `;
                cardGallery.appendChild(cardElement);
            });
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error);
        });
});

// Function to map card colors to actual CSS colors
function getColor(color) {
    switch (color.toUpperCase()) {
        case 'PURPLE':
            return '#9B59B6'; // A softer purple
        case 'BLUE':
            return '#3498DB'; // A bright blue
        case 'GREEN':
            return '#2ECC71'; // A fresh green
        case 'RED':
            return '#E74C3C'; // A vibrant red
        case 'RAINBOW':
            return 'linear-gradient(to right, #FF5733, #FFBD33, #75FF33, #33FF57, #33FFBD, #335BFF, #8E33FF)'; // A colorful rainbow gradient
        case 'ORANGE':
            return '#FF8C00'; // A bright orange
        case 'YELLOW':
            return '#F1C40F'; // A bright yellow
        case 'PINK':
            return '#FF69B4'; // A vibrant pink
        case 'CYAN':
            return '#00BFFF'; // A bright cyan
        case 'MAGENTA':
            return '#FF00FF'; // A bright magenta
        default:
            return '#FFFFFF'; // Default to white if color not recognized
    }
}