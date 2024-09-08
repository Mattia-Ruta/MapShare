function setURL(url) {
    window.history.pushState({}, "", url);
}
function moveMap(map, lat, lng) {
    console.log(`Moving map to ${lat}, ${lng}`);
    map.panTo({lat: lat, lng: lng});
}
function setMapcodeData(context, mapcode, territory) {
    const contextElem = document.getElementById("contextText");
    const mapcodeElem = document.getElementById("mapcodeText");
    contextElem.innerHTML = spinningGif;
    contextElem.innerHTML = spinningGif;
    if (context == "AAA") {
        contextElem.innerHTML = "";

        territoryElem.innerHTML = "International";
    } else {
        contextElem.innerHTML = context.toUpperCase();
        territoryElem.innerHTML = territory;
    }
    mapcodeElem.innerHTML = mapcode.toUpperCase();
    setURL(`/${context.toUpperCase()}/${mapcode.toUpperCase()}`);
}
function clearMapcodeData() {
    const territoryElem = document.getElementById("territory");
    const contextElem = document.getElementById("contextText");
    const mapcodeElem = document.getElementById("mapcodeText");
    contextElem.innerHTML = spinningGif;
    contextElem.innerHTML = spinningGif;
    mapcodeElem.innerHTML = "Loading...";
    territoryElem.innerHTML = "Loading...";
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

            // Add new marker
            currentMarker.map = null;
            let newCoordsLatLngObj = new google.maps.LatLng(lat, lng);
            let newMarker = new AdvancedMarkerElement({
                map: map,
                position: newCoordsLatLngObj,
                title: `${mapcodes[0].context} ${mapcodes[0].mapcode}`
            });
            currentMarker = newMarker;

            setMapcodeData(mapcodes[0].context, mapcodes[0].mapcode, mapcodes[0].territory);
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
        clearMapcodeData();

        // Get mapcode from new Coords
        ajaxGetMapcodeFromCoords(newCoords.lat(), newCoords.lng());
    });
    const mapReadyEvent = new CustomEvent("mapReady", {detail: map});
    document.dispatchEvent(mapReadyEvent);
}

initMap();

document.addEventListener("mapReady", (e) => {
    console.log("Map Loaded");
    const map = e.detail;
    if (pathArray.length == 0) {
        isFreshRequest = true;
        // Move map to general area of lookup data
        response = encode(defaultCoords.lat, defaultCoords.lng);
        if (response.length) {
            console.log("Fresh request, generating mapcode from general location:");
            bootstrapAlert("Mapcode generated from your general area", "info");
            console.log("Mapcodes using initial lat/lng: ", response);
            // First result is easiest
            mapcode.context = response[0].territoryAlphaCode;
            mapcode.mapcode = response[0].mapcode;
            setMapcodeData(mapcode.context, mapcode.mapcode, `${lookupData.region}, ${lookupData.country}`);
            moveMap(map, defaultCoords.lat, defaultCoords.lng);
        } else {
            // Unable to get a result, default to Big Ben
            setMapcodeData("GBR", "JJ.66", "United Kingdom");
            moveMap(map, 51.500675, -0.124578);
        }
    } else if (pathArray.length == 1) {
        console.log("Just mapcode given, let's see if it's the International context");
        mapcode.mapcode = pathArray[0];

        response = decode(mapcode.mapcode, "AAA");
        if (response) {
            console.log(`International Context - ${mapcode.mapcode}`);
            setMapcodeData("AAA", mapcode.mapcode, "International");
            moveMap(map, response.y, response.x);
            response = encode(response.y, response.x);
            if (response.length > 1) {
                // Easier mapcode here, let's suggest it
                let easierMapcodeInfo = response[0];
                let currentDomain = window.location.origin;
                bootstrapAlert(`The given mapcode is using the international context, try using mapcode ${easierMapcodeInfo.fullmapcode} (<a href="${currentDomain}/${easierMapcodeInfo.territoryAlphaCode}/${easierMapcodeInfo.mapcode}">${currentDomain}/${easierMapcodeInfo.territoryAlphaCode}/${easierMapcodeInfo.mapcode}</a>)`, "info");
            }
        } else {
            // Use context from request location
            console.log(`Not international, use context from request general area (${lookupData.context})`);
            response = decode(mapcode.mapcode, lookupData.context);
            if (response) {
                console.log(`Used context ${lookupData.context} for mapcode ${mapcode.mapcode}`);
                bootstrapAlert(`Used context ${lookupData.context} for mapcode ${mapcode.mapcode}`, "info");
                ajaxGetMapcodeFromCoords(response.y, response.x);
            } else {
                // Invalid
                console.error(`${mapcode.mapcode} is not a valid mapcode! Or at least needs context...`);
                bootstrapAlert(`${mapcode.mapcode} is not a valid mapcode, try again by providing a context (ex: https://mapshare.xyz/GBR/JJ.66)`);
                setMapcodeData("GBR", "JJ.66", "United Kingdom");
            }
        }
    } else if (pathArray.length == 2) {
        mapcode.context = pathArray[0];
        mapcode.mapcode = pathArray[1];
        response = decode(mapcode.mapcode, mapcode.context);
        if (response) {
            mapcode.context = pathArray[0];
            mapcode.mapcode = pathArray[1];
            response = decode(mapcode.mapcode, mapcode.context);
            if (response) {
                console.log(`Mapcode ${mapcode.context} ${mapcode.mapcode} found`);
                coords.lat = response.y;
                coords.lng = response.x;
                response = encode(coords.lat, coords.lng)[0];
                setMapcodeData(mapcode.context, mapcode.mapcode, territory);
                moveMap(map, coords.lat, coords.lng);
            }
        } else {
            // Invalid
            console.error(`${mapcode.context} ${mapcode.mapcode} is not a valid mapcode! Or at least needs context...`);
            bootstrapAlert(`${mapcode.mapcode} is not a valid mapcode, try again by providing a context (ex: https://mapshare.xyz/GBR/JJ.66)`);
            setMapcodeData("GBR", "JJ.66", "United Kingdom");
        }
    }
    
});

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
    const googleMapsLink = `https://www.google.com/maps/search/?api=1&query=${currentMarker._lngLat.lat}%2C${currentMarker._lngLat.lng}`;
    window.location.href = googleMapsLink;
});

// Copy Mapcode Functionality
const copyBtn = document.getElementById("copyBtn");
copyBtn.addEventListener("click", (e) => {
    const contextElem = document.getElementById("contextText");
    const mapcodeElem = document.getElementById("mapcodeText");
    const mapcodeText = `${contextElem.innerHTML} ${mapcodeElem.innerHTML}`;

    navigator.clipboard.writeText(mapcodeText);
    bootstrapAlert(`"${mapcodeText}" copied to clipboard!`, "info");
});