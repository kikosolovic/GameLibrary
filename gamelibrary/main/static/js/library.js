// ------------------------------------------------------
//  ACTIVE FILTER STATE
// ------------------------------------------------------
const activeFilters = {
    search: "",
    genre: "",
    priceMin: null,
    priceMax: null,
    scoreMin: null,
    scoreMax: null,
    sort: ""
};


// ------------------------------------------------------
//  DOM REFERENCES
// ------------------------------------------------------
const searchInput = document.getElementById("search-input");
const filtersBtn = document.getElementById("filters-btn");
const filtersPopup = document.getElementById("filters-popup");
const closeFilters = document.getElementById("close-filters");
const clearFilters = document.getElementById("clear-filters");
const applyFilters = document.getElementById("apply-filters");

const sortBtn = document.getElementById("sort-btn");
const sortPopup = document.getElementById("sort-popup");
let sortOptions = null;

const gameContainer = document.getElementById("game-container");


// ------------------------------------------------------
//  RENDER LOGIC
// ------------------------------------------------------
function renderGames(games) {

    gameContainer.classList.remove("show");
    gameContainer.classList.add("smooth-refresh");

    setTimeout(() => {
        gameContainer.innerHTML = "";

        if (!games || games.length === 0) {
            const p = document.createElement("p");
            p.classList.add("no-games");
            p.textContent = "No games found.";
            gameContainer.appendChild(p);

            requestAnimationFrame(() => {
                gameContainer.classList.add("show");
            });
            return;
        }

        // Create shelves of 15 games each
        for (let i = 0; i < games.length; i += 15) {
            const shelf = document.createElement("div");
            shelf.classList.add("shelf");

            games.slice(i, i + 15).forEach((game, index) => {
                const card = document.createElement("div");
                card.classList.add("game-card");
                card.dataset.appid = game.appid;

                // animation
                card.style.opacity = "0";
                card.style.transform = "translateY(6px)";
                card.style.transition = "opacity 0.25s ease, transform 0.25s ease";
                card.style.transitionDelay = `${index * 0.015}s`;

                card.innerHTML = `
                    <img src="${game.image}" 
                         alt="${game.name}" 
                         class="game-card-cover">
                    <div class="game-overlay">
                        <div class="game-title">${game.name}</div>
                    </div>
                `;

                // NEW: Direct navigation — no overlay injection
                card.addEventListener("click", () => {
                    window.location.href = `/game/${game.appid}/`;
                });

                shelf.appendChild(card);

                requestAnimationFrame(() => {
                    card.style.opacity = "1";
                    card.style.transform = "translateY(0)";
                });
            });

            gameContainer.appendChild(shelf);
        }

        requestAnimationFrame(() => {
            gameContainer.classList.add("show");
        });

    }, 10);
}


// ------------------------------------------------------
//  BUILD QUERYSTRING FROM ACTIVE FILTERS
// ------------------------------------------------------
function buildParams() {
    const params = new URLSearchParams();

    if (activeFilters.search) params.set("search", activeFilters.search);
    if (activeFilters.genre) params.set("genre", activeFilters.genre);

    if (activeFilters.priceMin != null) params.set("price_min", activeFilters.priceMin);
    if (activeFilters.priceMax != null) params.set("price_max", activeFilters.priceMax);

    if (activeFilters.scoreMin != null) params.set("score_min", activeFilters.scoreMin);
    if (activeFilters.scoreMax != null) params.set("score_max", activeFilters.scoreMax);

    if (activeFilters.sort) params.set("sort", activeFilters.sort);

    return params.toString();
}


// ------------------------------------------------------
//  FETCH + RENDER
// ------------------------------------------------------
function fetchAndRenderGames() {
    const qs = buildParams();
    const url = qs ? `/filter-games-api/?${qs}` : "/filter-games-api/";

    fetch(url)
        .then(res => {
            if (!res.ok) {
                throw new Error("Failed to fetch games");
            }
            return res.json();
        })
        .then(data => renderGames(data.results))
        .catch(err => {
            console.error(err);
            gameContainer.innerHTML = "<p class='no-games'>Error loading games.</p>";
        });
}


// ------------------------------------------------------
//  DOUBLE SLIDER LOGIC
// ------------------------------------------------------
function initDoubleSlider(sliderId, minLabelId, maxLabelId, setValuesCallback) {
    const slider = document.getElementById(sliderId);
    if (!slider) return;

    const rangeMin = slider.querySelector(".range-min");
    const rangeMax = slider.querySelector(".range-max");
    const labelMin = document.getElementById(minLabelId);
    const labelMax = document.getElementById(maxLabelId);

    if (!rangeMin || !rangeMax || !labelMin || !labelMax) return;

    function update() {
        let minVal = parseFloat(rangeMin.value);
        let maxVal = parseFloat(rangeMax.value);

        if (minVal > maxVal) {
            [minVal, maxVal] = [maxVal, minVal];
            rangeMin.value = minVal;
            rangeMax.value = maxVal;
        }

        labelMin.textContent = minVal;
        labelMax.textContent = maxVal;

        if (typeof setValuesCallback === "function") {
            setValuesCallback(minVal, maxVal);
        }
    }

    rangeMin.addEventListener("input", update);
    rangeMax.addEventListener("input", update);

    update();
}


// ------------------------------------------------------
//  INIT EVERYTHING
// ------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {

    sortOptions = document.querySelectorAll(".sort-option");

    // SEARCH
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            activeFilters.search = this.value.trim();
            fetchAndRenderGames();
        });
    }

    // FILTERS POPUP
    if (filtersBtn && filtersPopup && closeFilters) {
        filtersBtn.onclick = () => {
            if (sortPopup) sortPopup.classList.add("hidden");
            filtersPopup.classList.toggle("hidden");
        };

        closeFilters.onclick = () => {
            filtersPopup.classList.add("hidden");
        };
    }

    // SORT POPUP
    if (sortBtn && sortPopup) {
        sortBtn.onclick = () => {
            if (filtersPopup) filtersPopup.classList.add("hidden");

            const rect = sortBtn.getBoundingClientRect();
            sortPopup.style.top = `${rect.top + window.scrollY}px`;
            sortPopup.style.left = `${rect.right + 10}px`;

            sortPopup.classList.toggle("hidden");
        };
    }

    // SORT OPTION CLICK
    if (sortOptions) {
        sortOptions.forEach(btn => {
            btn.addEventListener("click", () => {
                activeFilters.sort = btn.dataset.sort || "";
                sortPopup.classList.add("hidden");
                fetchAndRenderGames();
            });
        });
    }

    // PRICE SLIDER
    initDoubleSlider("price-slider", "price-min-label", "price-max-label",
        (min, max) => {
            activeFilters.priceMin = min;
            activeFilters.priceMax = max;
        }
    );

    // SCORE SLIDER
    initDoubleSlider("score-slider", "score-min-label", "score-max-label",
        (min, max) => {
            activeFilters.scoreMin = min;
            activeFilters.scoreMax = max;
        }
    );

    // APPLY FILTERS
    if (applyFilters) {
        applyFilters.onclick = () => {
            const genreSelect = document.getElementById("filter-genre");
            if (genreSelect) activeFilters.genre = genreSelect.value;

            filtersPopup.classList.add("hidden");
            fetchAndRenderGames();
        };
    }

    // CLEAR FILTERS
    if (clearFilters) {
        clearFilters.onclick = () => {
            activeFilters.search = "";
            activeFilters.genre = "";
            activeFilters.priceMin = null;
            activeFilters.priceMax = null;
            activeFilters.scoreMin = null;
            activeFilters.scoreMax = null;
            activeFilters.sort = "";

            if (searchInput) searchInput.value = "";
            const genreSelect = document.getElementById("filter-genre");
            if (genreSelect) genreSelect.value = "";

            fetchAndRenderGames();
        };
    }

    // INITIAL LOAD
    fetchAndRenderGames();
});
