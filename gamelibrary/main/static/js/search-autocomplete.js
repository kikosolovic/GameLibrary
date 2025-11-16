
let searchTimeout;
const searchInput = document.querySelector('.search-bar input');
const searchDropdown = document.getElementById('searchDropdown');

if (!searchDropdown && searchInput) {
    const dropdown = document.createElement('div');
    dropdown.id = 'searchDropdown';
    dropdown.className = 'search-dropdown';
    searchInput.parentElement.appendChild(dropdown);
}

if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);
        
        if (query.length === 0) {
            hideSearchDropdown();
            return;
        }
        
        // debounce
        searchTimeout = setTimeout(() => {
            performLiveSearch(query);
        }, 300);
    });
    
    // Show dropdown again when clicking on search input if there's text
    searchInput.addEventListener('click', function(e) {
        const query = e.target.value.trim();
        if (query.length > 0) {
            performLiveSearch(query);
        }
    });
    
    // Show dropdown when focusing on input if there's text
    searchInput.addEventListener('focus', function(e) {
        const query = e.target.value.trim();
        if (query.length > 0) {
            performLiveSearch(query);
        }
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !document.getElementById('searchDropdown').contains(e.target)) {
            hideSearchDropdown();
        }
    });
}

function performLiveSearch(query) {
    const dropdown = document.getElementById('searchDropdown');
    
    dropdown.innerHTML = '<div class="search-loading">Searching...</div>';
    dropdown.classList.add('show');
    
    // AJAX search
    fetch(`/api/search/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data.results, query);
        })
        .catch(error => {
            console.error('Search error:', error);
            displaySearchResults(getDummySearchResults(query), query);
        });
}

function displaySearchResults(results, query) {
    const dropdown = document.getElementById('searchDropdown');
    
    if (results.length === 0) {
        dropdown.innerHTML = `
            <div class="search-no-results">
                No games found for "${query}"
            </div>
        `;
        dropdown.classList.add('show');
        return;
    }
    
    let html = `<div class="search-dropdown-header">Search results (${results.length})</div>`;
    
    // Show max 10 results
    const displayResults = results.slice(0, 10);
    
    displayResults.forEach(game => {
        html += `
            <div class="search-result-item" onclick="window.location.href='/game/${game.id}/'">
                <img src="${game.cover_image}" alt="${game.title}" class="search-result-image">
                <div class="search-result-info">
                    <div class="search-result-title">${game.title}</div>
                    <div class="search-result-meta">${game.genre || 'Game'}</div>
                </div>
            </div>
        `;
    });
    
    dropdown.innerHTML = html;
    dropdown.classList.add('show');
}

function hideSearchDropdown() {
    const dropdown = document.getElementById('searchDropdown');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
}

function getDummySearchResults(query) {
    const allGames = [
        {
            id: 1,
            title: 'The Legend of Zelda: Breath of the Wild',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Zelda',
            genre: 'Action-Adventure'
        },
        {
            id: 2,
            title: 'Elden Ring',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Elden',
            genre: 'RPG'
        },
        {
            id: 3,
            title: 'Stardew Valley',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Stardew',
            genre: 'Simulation'
        },
        {
            id: 4,
            title: 'Hollow Knight',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Hollow',
            genre: 'Action'
        },
        {
            id: 5,
            title: 'Celeste',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Celeste',
            genre: 'Platformer'
        },
        {
            id: 6,
            title: 'Hades',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Hades',
            genre: 'Rogue-like'
        },
        {
            id: 7,
            title: 'The Witcher 3: Wild Hunt',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Witcher',
            genre: 'RPG'
        },
        {
            id: 8,
            title: 'Red Dead Redemption 2',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=RDR2',
            genre: 'Action-Adventure'
        },
        {
            id: 9,
            title: 'Minecraft',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Minecraft',
            genre: 'Sandbox'
        },
        {
            id: 10,
            title: 'Undertale',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Undertale',
            genre: 'RPG'
        },
        {
            id: 11,
            title: 'Portal 2',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Portal',
            genre: 'Puzzle'
        },
        {
            id: 12,
            title: 'Dark Souls III',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=DarkSouls',
            genre: 'RPG'
        },
        {
            id: 13,
            title: 'Grand Theft Auto V',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=GTA5',
            genre: 'Action'
        },
        {
            id: 14,
            title: 'Terraria',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Terraria',
            genre: 'Sandbox'
        },
        {
            id: 15,
            title: 'Bloodborne',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodborne',
            genre: 'Action RPG'
        },
        {
            id: 16,
            title: 'Blood Bowl 2',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=BloodBowl',
            genre: 'Sports'
        },
        {
            id: 17,
            title: 'Bloons TD 6',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloons',
            genre: 'Tower Defense'
        },
        {
            id: 18,
            title: 'Bloodstained: Ritual of the Night',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodstained',
            genre: 'Metroidvania'
        },
        {
            id: 19,
            title: 'Bloober Team Collection',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloober',
            genre: 'Horror'
        },
        {
            id: 20,
            title: 'Blockland',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Blockland',
            genre: 'Sandbox'
        },
        {
            id: 21,
            title: 'Bloodroots',
            cover_image: 'https://via.placeholder.com/90x120/3b2a20/f5e1c8?text=Bloodroots',
            genre: 'Action'
        },
    ];
    
    // Filter games by query
    return allGames.filter(game => 
        game.title.toLowerCase().includes(query.toLowerCase())
    );
}