import { useEffect, useCallback, useState, useMemo } from "react";
import { GoogleMap, useJsApiLoader, HeatmapLayer, Marker, InfoWindow } from "@react-google-maps/api";
import { analyticsAPI } from "../services/api";

const MAP_OPTIONS = {
  disableDefaultUI: true,
  zoomControl: true,
  styles: [
    { elementType: "geometry",        stylers: [{ color: "#0f172a" }] },
    { elementType: "labels.text.fill",stylers: [{ color: "#94a3b8" }] },
    { featureType: "road",            elementType: "geometry", stylers: [{ color: "#1e293b" }] },
    { featureType: "road",            elementType: "geometry.stroke", stylers: [{ color: "#0f172a" }] },
    { featureType: "water",           elementType: "geometry", stylers: [{ color: "#020617" }] },
    { featureType: "poi",             stylers: [{ visibility: "off" }] },
  ],
};

const LIBRARIES = ["visualization"];

export default function LiveHeatmap({ results = [] }) {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: import.meta.env.VITE_GOOGLE_MAPS_KEY,
    libraries: LIBRARIES,
  });

  const [heatmapData, setHeatmapData] = useState([]);
  const [heatmapPoints, setHeatmapPoints] = useState([]);
  const [selectedLot, setSelectedLot] = useState(null);
  const [center, setCenter] = useState({ lat: 13.0827, lng: 80.2707 }); // Default: Chennai
  const [layerType, setLayerType] = useState("occupancy"); // "occupancy" | "revenue" | "demand"
  const [userLocation, setUserLocation] = useState(null);
  const [locating, setLocating] = useState(false);
  const [geoError, setGeoError] = useState("");

  // Build from search results or fetch from API
  useEffect(() => {
    if (results.length > 0) {
      if (window.google) {
        const points = results.map((lot) => ({
          location: new window.google.maps.LatLng(lot.latitude, lot.longitude),
          weight: (lot.occupancy_rate != null ? lot.occupancy_rate : 0.5) * 5,
        }));
        setHeatmapData(points);
        setCenter({ lat: results[0].latitude, lng: results[0].longitude });
      }
    } else {
      // Fetch full heatmap from API
      analyticsAPI.heatmap(layerType).then(({ data }) => {
        setHeatmapPoints(data);
        if (window.google) {
          const points = data.map((p) => ({
            location: new window.google.maps.LatLng(p.lat, p.lng),
            weight: p.weight * 5,
          }));
          setHeatmapData(points);
          if (data.length > 0) {
            setCenter({ lat: data[0].lat, lng: data[0].lng });
          }
        }
      }).catch(() => {});
    }
  }, [results, isLoaded, layerType]);

  const lots = useMemo(() => {
    return results.length > 0 ? results : heatmapPoints;
  }, [results, heatmapPoints]);

  const applyLocation = useCallback((position, source = "gps") => {
    const nextLocation = {
      lat: position.coords.latitude,
      lng: position.coords.longitude,
    };

    setUserLocation(nextLocation);
    setCenter(nextLocation);
    setLocating(false);

    if (source === "approximate") {
      setGeoError("Showing an approximate location because browser location access is unavailable.");
    } else {
      setGeoError("");
    }
  }, []);

  const fallbackToApproximateLocation = useCallback(async () => {
    try {
      const response = await fetch("https://ipapi.co/json/");
      const data = await response.json();
      if (data.latitude != null && data.longitude != null) {
        applyLocation({ coords: { latitude: data.latitude, longitude: data.longitude } }, "approximate");
        return;
      }
    } catch (error) {
      console.warn("Approximate location fallback failed:", error);
    }

    setLocating(false);
    setGeoError("Unable to determine your location. Please allow location access or try again.");
  }, [applyLocation]);

  useEffect(() => {
    if (!isLoaded) return;

    if (!navigator.geolocation) {
      setGeoError("Geolocation is not supported by this browser.");
      return;
    }

    setLocating(true);
    setGeoError("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        applyLocation(position);
      },
      (error) => {
        console.warn("Auto geolocation unavailable:", error);
        fallbackToApproximateLocation();
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, [applyLocation, fallbackToApproximateLocation, isLoaded]);

  const findMyLocation = useCallback(() => {
    if (!navigator.geolocation) {
      setGeoError("Geolocation is not supported by this browser.");
      return;
    }

    setLocating(true);
    setGeoError("");

    navigator.geolocation.getCurrentPosition(
      (position) => applyLocation(position),
      (error) => {
        console.error("Geolocation failed:", error);
        fallbackToApproximateLocation();
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, [applyLocation, fallbackToApproximateLocation]);

  if (!isLoaded) {
    return (
      <div className="glass-card h-[500px] flex items-center justify-center text-slate-400">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          Loading Map...
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden" style={{ height: "550px" }}>
      <div className="px-4 py-3 border-b border-white/8 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-white">Live Demand Heatmap</h3>
          {results.length === 0 && (
            <select
              value={layerType}
              onChange={(e) => setLayerType(e.target.value)}
              className="bg-slate-900/80 border border-white/10 text-white rounded-lg px-2.5 py-1 text-xs focus:outline-none focus:border-primary-500/50 cursor-pointer"
            >
              <option value="occupancy">Occupancy Rate</option>
              <option value="revenue">Revenue Density</option>
              <option value="demand">Demand Forecast</option>
            </select>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-400">
          <button
            type="button"
            onClick={findMyLocation}
            disabled={locating}
            className="inline-flex items-center gap-1.5 rounded-lg border border-primary-500/30 bg-primary-500/10 px-3 py-1.5 text-primary-200 hover:bg-primary-500/20 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {locating ? "Locating..." : "📍 Find my location"}
          </button>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-emerald-500" /> Low (0–40%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500" /> Medium (40–70%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500" /> High (70–100%)
          </span>
        </div>
      </div>

      <GoogleMap
        mapContainerStyle={{ width: "100%", height: "calc(100% - 49px)" }}
        center={center}
        zoom={14}
        options={MAP_OPTIONS}
      >
        {userLocation && (
          <Marker
            position={userLocation}
            icon={{
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 8,
              fillColor: "#38bdf8",
              fillOpacity: 1,
              strokeColor: "#ffffff",
              strokeWeight: 2,
            }}
          />
        )}
        {heatmapData.length > 0 && (
          <HeatmapLayer
            data={heatmapData}
            options={{ radius: 40, opacity: 0.7 }}
          />
        )}

        {lots.map((lot) => {
          const lat = lot.latitude || lot.lat;
          const lng = lot.longitude || lot.lng;
          if (!lat || !lng) return null;

          const available = lot.available_slots != null ? lot.available_slots : lot.available;
          
          return (
            <Marker
              key={lot.lot_id}
              position={{ lat, lng }}
              onClick={() => setSelectedLot(lot)}
              icon={{
                url: available > 0
                  ? "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(
                      `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                        <circle cx="16" cy="16" r="14" fill="#22c55e" opacity="0.9"/>
                        <text x="16" y="21" text-anchor="middle" fill="white" font-size="14" font-weight="bold">P</text>
                      </svg>`
                    )
                  : "data:image/svg+xml;charset=UTF-8," + encodeURIComponent(
                      `<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                        <circle cx="16" cy="16" r="14" fill="#ef4444" opacity="0.9"/>
                        <text x="16" y="21" text-anchor="middle" fill="white" font-size="14" font-weight="bold">P</text>
                      </svg>`
                    ),
                scaledSize: new window.google.maps.Size(32, 32),
              }}
            />
          );
        })}

        {selectedLot && (
          <InfoWindow
            position={{
              lat: selectedLot.latitude || selectedLot.lat,
              lng: selectedLot.longitude || selectedLot.lng,
            }}
            onCloseClick={() => setSelectedLot(null)}
          >
            <div className="text-gray-900 p-2 min-w-[200px]">
              <div className="font-semibold text-sm mb-1">{selectedLot.lot_name}</div>
              <div className="text-xs text-gray-600 mb-2">{selectedLot.address || "Active Parking"}</div>
              <div className="space-y-1 text-xs border-t border-gray-100 pt-2">
                {selectedLot.price_per_hour != null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Price:</span>
                    <span className="font-semibold">₹{selectedLot.price_per_hour}/hr</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-500">Free Slots:</span>
                  <span className={`font-semibold ${(selectedLot.available_slots != null ? selectedLot.available_slots : selectedLot.available) > 0 ? "text-green-600" : "text-red-600"}`}>
                    {selectedLot.available_slots != null ? selectedLot.available_slots : selectedLot.available} / {selectedLot.total_slots || "—"}
                  </span>
                </div>
                {selectedLot.occupancy_rate != null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Occupancy:</span>
                    <span className="font-semibold">{selectedLot.occupancy_rate}%</span>
                  </div>
                )}
                {selectedLot.revenue_density != null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Rev. Density:</span>
                    <span className="font-semibold">₹{selectedLot.revenue_density}/slot</span>
                  </div>
                )}
                {selectedLot.demand_forecast_score != null && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Forecast:</span>
                    <span className="font-semibold">{(selectedLot.demand_forecast_score * 100).toFixed(0)}% demand</span>
                  </div>
                )}
              </div>
            </div>
          </InfoWindow>
        )}
      </GoogleMap>
      {geoError && <p className="px-4 pb-3 text-xs text-amber-300">{geoError}</p>}
    </div>
  );
}
