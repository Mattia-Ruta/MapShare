// region Function Definitions
function setURL(url) {
    window.history.pushState({}, "", url);
}
function moveMap(map, lat, lng) {
    console.log(`Moving map to ${lat}, ${lng}`);
    map.panTo({lat: lat, lng: lng});
}
function setMapcodeData(context, mapcode, territory, altMapcodes = [], countryFlag = "") {
    const territoryElem = document.getElementById("territory");
    const contextElem = document.getElementById("contextText");
    const mapcodeElem = document.getElementById("mapcodeText");
    const altMapcodesDropdown = document.getElementById("altMapcodesDropdown");
    const countryFlagElem = document.getElementById("countryFlag");
    console.log(altMapcodes);
    contextElem.innerHTML = spinningGif;
    contextElem.innerHTML = spinningGif;
    context = context.toUpperCase();
    mapcode = mapcode.toUpperCase();
    if (context == "AAA") {
        contextElem.innerHTML = "AAA";
        territoryElem.innerHTML = "International";
        countryFlagElem.innerHTML = "🌐";
    } else {
        contextElem.innerHTML = context;
        territoryElem.innerHTML = territory;
        countryFlagElem.innerHTML = countryFlag;
    }
    mapcodeElem.innerHTML = mapcode.toUpperCase();
    setURL(`/${context}/${mapcode}`);
    for (const altMapcode of altMapcodes) {
        if (typeof altMapcode.countryFlag == "undefined") altMapcode.countryFlag = "";
        if (altMapcode.mapcode == mapcode) {
            altMapcodesDropdown.innerHTML += `<li><a class="dropdown-item active" href="/${context}/${mapcode}" aria-current="true">${altMapcode.countryFlag}[${context} ${mapcode}] <small><i>${territory}</i></small></a></li>`;
        } else {
            altMapcodesDropdown.innerHTML += `<li><a class="dropdown-item" href="/${altMapcode.context}/${altMapcode.mapcode}">${altMapcode.countryFlag} [${altMapcode.context} ${altMapcode.mapcode}] <small><i>${altMapcode.territory}</i></small></a></li>`;
        }
    }
}
function clearMapcodeData() {
    const territoryElem = document.getElementById("territory");
    const contextElem = document.getElementById("contextText");
    const mapcodeElem = document.getElementById("mapcodeText");
    const altMapcodesDropdown = document.getElementById("altMapcodesDropdown");
    const countryFlagElem = document.getElementById("countryFlag");
    contextElem.innerHTML = spinningGif;
    contextElem.innerHTML = spinningGif;
    mapcodeElem.innerHTML = "Loading...";
    territoryElem.innerHTML = "Loading...";
    altMapcodesDropdown.innerHTML = "";
    countryFlagElem.innerHTML = "";
}
function bootstrapAlert(alertMsg, level = "danger") {
    const alertContainer = document.getElementById("alert-container");
    const alertWrapper = document.createElement("div");
    alertContainer.innerHTML = "";
    alertWrapper.innerHTML = `<div class="container"><div class="alert alert-${level} alert-dismissible" role="alert" style="margin-top: 4em;"><div>${alertMsg}</div><button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div></div>`;
    alertContainer.append(alertWrapper);
    setTimeout(function() {
        alertContainer.innerHTML = "";
    }, 7000);
}
function clearBootstrapAlert() {
    const alertContainer = document.getElementById("alert-container");
    setTimeout(function() {
        alertContainer.innerHTML = "";
    }, 7000);
}
async function ajaxGetMapcodeFromCoords(lat, lng) {
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    const errorMsg = "An error has occured, please refresh the page and try again";
    clearMapcodeData();
    const response = await fetch("/getMapcodeAJAX", {
        method: "POST",
        headers: {"X-CSRFToken": csrfToken},
        body: JSON.stringify({
            lat: lat,
            lng: lng
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.mapcodes.length) {
            const mapcodes = data.mapcodes;
            const newMapcode = mapcodes[0];

            // Add new marker
            currentMarker.map = null;
            let newCoordsLatLngObj = new google.maps.LatLng(lat, lng);
            let newMarker = new AdvancedMarkerElement({
                map: map,
                position: newCoordsLatLngObj,
                title: `${newMapcode.context} ${newMapcode.mapcode}`
            });
            currentMarker = newMarker;

            setMapcodeData(newMapcode.context, newMapcode.mapcode, newMapcode.territory, mapcodes, newMapcode.countryFlag);
            mapcode = newMapcode.mapcode;
            context = newMapcode.context;
            territory = newMapcode.territory;
            moveMap(map, lat, lng);
            if (debug) console.log("Mapcodes from Coords: ", mapcodes);
        } else {
            console.error(data.error)
            alert(errorMsg);
        }
    })
    .catch((error) => {
        console.error(`Error: ${error}`);
        bootstrapAlert("Sorry, couldn't get a mapcode from given location");
    });
}

let map;
async function initMap() {
    const { Map } = await google.maps.importLibrary("maps");
    const { AdvancedMarkerElement } = await google.maps.importLibrary("marker");
    const defaultCoordsLatLngObj = new google.maps.LatLng(coords.lat, coords.lng);
    
    map = new Map(document.getElementById("map"), {
        center: defaultCoords,
        zoom: 15,
        center: defaultCoordsLatLngObj,
        mapId: "map",
        zoomControl: true,
        streetViewControl: false,
        mapTypeControl: true,
        rotateControl: true,
        mapTypeId: "hybrid"
    });

    // Default Marker
    const defaultMarker = new AdvancedMarkerElement({
        map: map,
        position: defaultCoordsLatLngObj,
        title: `${mapcode.context} ${mapcode.mapcode}`
    });
    currentMarker = defaultMarker;

    map.addListener("click", (e) => {
        const newCoords = e.latLng;
        console.log("New coordinates: ", newCoords.lat(), newCoords.lng());

        // Get mapcode from new Coords
        ajaxGetMapcodeFromCoords(newCoords.lat(), newCoords.lng());
    });
    return map;
}

// region Setup
clearBootstrapAlert();
setURL(`/${context}/${mapcode}`);

initMap()
.then((map) => {
    console.log("Map Loaded");

    // region Top-Right Buttons
    // Location Button
    const locationBtn = document.getElementById("locationBtn");
    locationBtn.addEventListener("click", (e) => {
        if ("geolocation" in navigator) {
            function locationSuccess(position) {
                const coords = position.coords;
                ajaxGetMapcodeFromCoords(coords.latitude, coords.longitude);
                console.log(`New coordinates: ${coords.latitude}, ${coords.longitude}`);
            }
            function locationError() {
                bootstrapAlert("Sorry, position can't be found", "danger");
            }
    
            const locationOptions = {
                enableHighAccuracy: true,
                maximumAge: 30000,
                timeout: 27000
            };
            navigator.geolocation.getCurrentPosition(locationSuccess, locationError, locationOptions);
        } else {
            bootstrapAlert("Location services not available");
        }
    });
    
    // Share Button
    const shareBtn = document.getElementById("shareBtn");
    shareBtn.addEventListener("click", (e) => {
        const contextElem = document.getElementById("contextText");
        const mapcodeTextElem = document.getElementById("mapcodeText");
        if (navigator.share) {
            navigator.share({
                title: `Mapshare - Exact location in ${territoryElem.innerHTML} (${contextElem.innerHTML} ${mapcodeTextElem.innerHTML})`,
                url: window.location.href
            });
        } else {
            navigator.clipboard.writeText(window.location.href);
            bootstrapAlert("Share link copied to clipboard!", "info");
            console.error("Share functionality not available in this browser");
        }
    });
    
    // Google Maps Button
    const googleMapsBtn = document.getElementById("googleMapsBtn");
    googleMapsBtn.addEventListener("click", (e) => {
        console.log(currentMarker.position.lat)
        const googleMapsLink = `https://www.google.com/maps/search/?api=1&query=${currentMarker.position.lat}%2C${currentMarker.position.lng}`;
        window.location.href = googleMapsLink;
    });
    
    // Copy Mapcode Functionality
    const copyBtn = document.getElementById("copyBtn");
    copyBtn.addEventListener("click", (e) => {
        const mapcodeText = `${context} ${mapcode}`;
        navigator.clipboard.writeText(mapcodeText);
        bootstrapAlert(`"${mapcodeText}" copied to clipboard!`, "info");
    });
});
