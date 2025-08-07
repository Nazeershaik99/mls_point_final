// MLS Point Locator JavaScript
document.addEventListener("DOMContentLoaded", function () {
  if (document.body.classList.contains('mls-page')) {
    // --- Initialization ---
    let map = L.map('map').setView([16.5, 80.6], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(map);

    let mlsMarkers = [];
    let currentPopup = null;

    // --- Status Banner ---
    function showStatus(message, type = "info") {
      const banner = document.getElementById("statusBanner");
      if (banner) {
        banner.className = `status-message ${type}`;
        banner.textContent = message;
        banner.style.display = "block";
        setTimeout(() => (banner.style.display = "none"), 5000);
      }
    }

    // --- Fetch Current User ---
    function updateUserInfo() {
      const currentUserElement = document.getElementById('currentUser');
      const currentTimeElement = document.getElementById('currentTime');

      fetch('/api/user')
        .then(res => res.json())
        .then(data => {
          if (currentUserElement) {
            currentUserElement.textContent = data.username || "Unknown";
          }
          if (currentTimeElement) {
            currentTimeElement.textContent = data.timestamp || "";
          }
        })
        .catch(error => {
          console.error('Error fetching user info:', error);
          showStatus("Error loading user information", "error");
        });
    }

    // Only call if elements exist
    if (document.getElementById('currentUser') || document.getElementById('currentTime')) {
      updateUserInfo();
    }

    // --- Load District Dropdown ---
    const districtSelect = document.getElementById("district");
    const mandalSelect = document.getElementById("mandal");
    const loadBtn = document.getElementById("loadBtn");

    if (districtSelect) {
      fetch('/api/districts')
        .then(res => res.json())
        .then(districts => {
          districtSelect.innerHTML = `<option value="">Choose a district...</option>`;
          districts.forEach(district => {
            districtSelect.innerHTML += `<option value="${district}">${district}</option>`;
          });
          districtSelect.disabled = false;
        })
        .catch(error => {
          console.error('Error loading districts:', error);
          showStatus("Error loading districts", "error");
        });
    }

    // --- District Change Handler ---
    if (districtSelect && mandalSelect) {
      districtSelect.addEventListener('change', function() {
        mandalSelect.innerHTML = `<option value="">Choose a mandal...</option>`;
        mandalSelect.disabled = true;
        if (loadBtn) loadBtn.disabled = true;

        if (!this.value) return;

        fetch(`/api/mandals/${this.value}`)
          .then(res => res.json())
          .then(mandals => {
            mandalSelect.innerHTML = `<option value="">Choose a mandal...</option>`;
            mandals.forEach(mandal => {
              mandalSelect.innerHTML += `<option value="${mandal}">${mandal}</option>`;
            });
            mandalSelect.disabled = false;
          })
          .catch(error => {
            console.error('Error loading mandals:', error);
            showStatus("Error loading mandals", "error");
          });
      });
    }

    // --- Mandal Change Handler ---
    if (mandalSelect && loadBtn) {
      mandalSelect.addEventListener('change', function() {
        loadBtn.disabled = !this.value;
      });
    }

    // --- Create Enhanced Popup Content ---
    // Update the createPopupContent function
function createPopupContent(point) {
    return `
        <div class="popup-content">
            <div class="popup-title">${point.mls_point_name || ''}</div>
            <div class="popup-info">
                <strong>Code:</strong> ${point.mls_point_code || ''}<br>
                <strong>District:</strong> ${point.district_name || ''}<br>
                <strong>Mandal:</strong> ${point.mandal_name || ''}<br>
                <strong>Incharge:</strong> ${point.mls_point_incharge_name || ''}<br>
                <strong>Contact:</strong> ${point.mls_point_incharge_mobile_no || ''}
            </div>
            <div class="popup-actions">
                <a href="/view_details/${point.mls_point_code}" class="popup-btn" target="_blank">
                    <i class="fas fa-info-circle"></i> View Details
                </a>
            </div>
        </div>
    `;
}

// Add search functionality
const searchInput = document.getElementById('mlsCodeSearch');
if (searchInput) {
    searchInput.addEventListener('input', debounce(function() {
        const searchTerm = this.value.trim();
        if (searchTerm.length < 2) return;

        fetch(`/api/search_mls/${encodeURIComponent(searchTerm)}`)
            .then(res => res.json())
            .then(points => {
                clearMarkers();
                if (points.length === 0) {
                    showStatus("No MLS points found", "warning");
                    return;
                }

                points.forEach(point => {
                    if (point.mls_point_latitude && point.mls_point_longitude) {
                        let lat = parseFloat(point.mls_point_latitude);
                        let lng = parseFloat(point.mls_point_longitude);

                        if (!isNaN(lat) && !isNaN(lng)) {
                            let marker = L.marker([lat, lng]).addTo(map);
                            marker.bindPopup(createPopupContent(point));
                            mlsMarkers.push(marker);
                        }
                    }
                });

                if (mlsMarkers.length > 0) {
                    map.fitBounds(L.featureGroup(mlsMarkers).getBounds(), { padding: [40, 40] });
                    showStatus(`Found ${points.length} MLS points`, "success");
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                showStatus("Error performing search", "error");
            });
    }, 300));
}

// Debounce function to limit API calls
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func.apply(this, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

    // --- Load MLS Points ---
    function clearMarkers() {
      mlsMarkers.forEach(marker => map.removeLayer(marker));
      mlsMarkers = [];
    }

    function updateStats(points) {
      const totalPointsElement = document.getElementById('totalPoints');
      const activePointsElement = document.getElementById('activePoints');

      if (totalPointsElement) {
        totalPointsElement.textContent = points.length;
      }
      if (activePointsElement) {
        activePointsElement.textContent = points.filter(p => p.status && p.status.toLowerCase() === 'active').length;
      }
    }

    window.loadMLSPoints = function() {
      clearMarkers();
      if (!districtSelect || !mandalSelect) return;

      const district = districtSelect.value;
      const mandal = mandalSelect.value;

      if (!district || !mandal) {
        showStatus("Please select both district and mandal", "error");
        return;
      }

      showStatus("Loading MLS Points...", "info");

      fetch(`/api/mls_points/${encodeURIComponent(district)}/${encodeURIComponent(mandal)}`)
        .then(res => {
          if (!res.ok) {
            return res.json().then(err => {
              throw new Error(err.error || `HTTP error! status: ${res.status}`);
            });
          }
          return res.json();
        })
        .then(points => {
          console.log("Received points:", points); // Debug log

          if (!Array.isArray(points)) {
            throw new Error("Invalid response format");
          }

          if (points.length === 0) {
            showStatus("No MLS points found for selected location", "warning");
            updateStats([]);
            return;
          }

          updateStats(points);

          points.forEach(point => {
            if (point.mls_point_latitude && point.mls_point_longitude) {
              let lat = parseFloat(point.mls_point_latitude);
              let lng = parseFloat(point.mls_point_longitude);

              console.log(`Processing point ${point.mls_point_code}: ${lat}, ${lng}`); // Debug log

              if (!isNaN(lat) && !isNaN(lng) &&
                  lat >= -90 && lat <= 90 &&
                  lng >= -180 && lng <= 180) {
                let marker = L.marker([lat, lng]).addTo(map);
                marker.bindPopup(createPopupContent(point));
                mlsMarkers.push(marker);
              } else {
                console.warn(`Invalid coordinates for MLS point ${point.mls_point_code}: ${lat}, ${lng}`);
              }
            } else {
              console.warn(`Missing coordinates for MLS point ${point.mls_point_code}`);
            }
          });

          if (mlsMarkers.length > 0) {
            map.fitBounds(L.featureGroup(mlsMarkers).getBounds(), { padding: [40, 40] });
            showStatus(`Loaded ${mlsMarkers.length} MLS points`, "success");
          } else {
            showStatus("No valid coordinates found for MLS points", "warning");
          }
        })
        .catch(error => {
          console.error('Error loading MLS points:', error);
          showStatus(`Error: ${error.message}`, "error");
        });
    };
    // Add this function to handle MLS code search more effectively
function searchByMLSCode() {
    const searchTerm = document.getElementById('mlsCodeSearch').value.trim();
    if (searchTerm.length < 1) {
        showStatus("Please enter an MLS Point Code to search", "warning");
        return;
    }

    showStatus("Searching for MLS Point...", "info");
    clearMarkers();

    fetch(`/api/search_mls/${encodeURIComponent(searchTerm)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(points => {
            if (!Array.isArray(points)) {
                throw new Error("Invalid response format");
            }

            if (points.length === 0) {
                showStatus("No MLS points found matching your search", "warning");
                return;
            }

            points.forEach(point => {
                if (point.mls_point_latitude && point.mls_point_longitude) {
                    let lat = parseFloat(point.mls_point_latitude);
                    let lng = parseFloat(point.mls_point_longitude);

                    if (!isNaN(lat) && !isNaN(lng)) {
                        let marker = L.marker([lat, lng]).addTo(map);
                        marker.bindPopup(createPopupContent(point));
                        mlsMarkers.push(marker);
                    }
                }
            });

            if (mlsMarkers.length > 0) {
                map.fitBounds(L.featureGroup(mlsMarkers).getBounds(), { padding: [40, 40] });
                showStatus(`Found ${points.length} MLS points`, "success");
            } else {
                showStatus("Found MLS points but no valid coordinates", "warning");
            }
        })
        .catch(error => {
            console.error('Search error:', error);
            showStatus(`Error: ${error.message}`, "error");
        });
}

// Function to clear search
function clearSearch() {
    document.getElementById('mlsCodeSearch').value = '';
    clearMarkers();
    showStatus("Search cleared", "info");
}

// Improved popup content creation with more information
function createPopupContent(point) {
    return `
        <div class="popup-content">
            <div class="popup-title">${point.mls_point_name || ''}</div>
            <div class="popup-info">
                <strong>Code:</strong> ${point.mls_point_code || ''}<br>
                <strong>District:</strong> ${point.district_name || ''}<br>
                <strong>Mandal:</strong> ${point.mandal_name || ''}<br>
                <strong>Incharge:</strong> ${point.mls_point_incharge_name || ''}<br>
                <strong>Contact:</strong> ${point.phone_number || ''}
            </div>
            <div class="popup-actions">
                <a href="/view_details/${point.mls_point_code}" class="popup-btn">
                    <i class="fas fa-info-circle"></i> View Details
                </a>
            </div>
        </div>
    `;
}
    // Initialize stats
    updateStats([]);
  }
});