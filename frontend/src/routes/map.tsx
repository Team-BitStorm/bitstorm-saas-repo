import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  MapContainer,
  TileLayer,
  Marker,
  Circle,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import MarkerClusterGroup from "react-leaflet-cluster";
import "react-leaflet-cluster/dist/assets/MarkerCluster.css";
import "react-leaflet-cluster/dist/assets/MarkerCluster.Default.css";

import { useAuth } from "@/lib/auth-context";
import {
  discoverProviders,
  fetchAllCustomerApproxLocations,
  fetchHomeLocation,
  type ApproxCustomerListItem,
  type MarketplaceProvider,
} from "@/lib/marketplace-api";

export const Route = createFileRoute("/map")({
  component: MapPage,
});

// Fix Leaflet default icon paths that Vite breaks
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const BLUE_ICON = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

/** Flies to the given coordinates once on first render */
function FlyTo({ lat, lng, zoom = 12 }: { lat: number; lng: number; zoom?: number }) {
  const map = useMap();
  const moved = useRef(false);
  useEffect(() => {
    if (!moved.current) {
      map.flyTo([lat, lng], zoom, { duration: 1 });
      moved.current = true;
    }
  }, [lat, lng, zoom, map]);
  return null;
}

/** Provider marker + travel-radius circle (customer view) */
function ProviderLayer({
  provider,
  t,
}: {
  provider: MarketplaceProvider;
  t: ReturnType<typeof useTranslation>["t"];
}) {
  const lat = Number(provider.service_area?.latitude);
  const lng = Number(provider.service_area?.longitude);
  if (!lat || !lng) return null;

  return (
    <>
      <Marker position={[lat, lng]} icon={BLUE_ICON}>
        <Popup>
          <div style={{ minWidth: 180 }}>
            <p style={{ fontWeight: 600, marginBottom: 2 }}>{provider.display_name}</p>
            {provider.service_area?.city ? (
              <p style={{ fontSize: 13, color: "#666", marginBottom: 4 }}>
                {provider.service_area.city}
                {provider.service_area.region ? `, ${provider.service_area.region}` : ""}
              </p>
            ) : null}
            {provider.travel_radius_km ? (
              <p style={{ fontSize: 13 }}>
                {t("map.travelRadius", { km: provider.travel_radius_km })}
              </p>
            ) : null}
            {provider.offerings.slice(0, 3).map((o) => (
              <p key={o.id} style={{ fontSize: 13 }}>
                {o.service.name} — {o.provider_price} RON
              </p>
            ))}
            {provider.distance_km ? (
              <p style={{ fontSize: 13, fontWeight: 600, marginTop: 4 }}>
                {t("marketplace.distanceKm", { km: provider.distance_km })}
              </p>
            ) : null}
          </div>
        </Popup>
      </Marker>
      {provider.travel_radius_km ? (
        <Circle
          center={[lat, lng]}
          radius={provider.travel_radius_km * 1000}
          pathOptions={{ color: "#3b82f6", fillOpacity: 0.05, weight: 1.5 }}
        />
      ) : null}
    </>
  );
}

function MapPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isProvider = user?.role === "provider";

  // Browser geolocation (used to centre the map)
  const [geoCenter, setGeoCenter] = useState<[number, number] | null>(null);
  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setGeoCenter([pos.coords.latitude, pos.coords.longitude]),
      () => {/* permission denied or unavailable — fall back to defaults */},
      { timeout: 6000 },
    );
  }, []);

  const homeQuery = useQuery({
    queryKey: ["home-location"],
    queryFn: fetchHomeLocation,
    enabled: !isProvider,
  });

  const providersQuery = useQuery({
    queryKey: ["providers-map"],
    queryFn: () => discoverProviders(),
    enabled: !isProvider,
  });

  const customersQuery = useQuery({
    queryKey: ["customers-approx"],
    queryFn: fetchAllCustomerApproxLocations,
    enabled: isProvider,
  });

  // Priority for initial centre: browser GPS → stored home → Romania default
  const homeLat = homeQuery.data?.latitude ? Number(homeQuery.data.latitude) : null;
  const homeLng = homeQuery.data?.longitude ? Number(homeQuery.data.longitude) : null;
  const flyTarget: [number, number] | null =
    geoCenter ?? (homeLat && homeLng ? [homeLat, homeLng] : null);
  const defaultCenter: [number, number] = [46.77, 23.59];

  const customers: ApproxCustomerListItem[] = customersQuery.data ?? [];

  return (
    <div className="space-y-4">
      <header>
        <h1 className="font-display text-4xl">
          {isProvider ? t("map.providerTitle") : t("map.customerTitle")}
        </h1>
        <p className="text-muted-foreground mt-2">
          {isProvider ? t("map.providerSubtitle") : t("map.customerSubtitle")}
        </p>
      </header>

      <div
        className="rounded-3xl overflow-hidden border-2 border-border"
        style={{ height: "70vh", minHeight: 420 }}
      >
        <MapContainer
          center={flyTarget ?? defaultCenter}
          zoom={flyTarget ? 12 : 7}
          style={{ height: "100%", width: "100%" }}
          scrollWheelZoom
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {flyTarget ? <FlyTo lat={flyTarget[0]} lng={flyTarget[1]} /> : null}

          {/* ── Customer view: provider markers + travel-radius circles ── */}
          {!isProvider
            ? (providersQuery.data ?? []).map((provider) => (
                <ProviderLayer key={provider.id} provider={provider} t={t} />
              ))
            : null}

          {/* ── Provider view: clustered customer markers (Markers only inside cluster) ── */}
          {isProvider ? (
            <>
              {/* Uncertainty circles rendered outside the cluster group */}
              {customers.map((c) => (
                <Circle
                  key={`circle-${c.customer_id}`}
                  center={[c.approx_lat, c.approx_lng]}
                  radius={c.radius_m}
                  pathOptions={{ color: "#3b82f6", fillOpacity: 0.08, weight: 1.5 }}
                />
              ))}

              {/* Only Markers go inside MarkerClusterGroup */}
              <MarkerClusterGroup chunkedLoading>
                {customers.map((c) => (
                  <Marker
                    key={c.customer_id}
                    position={[c.approx_lat, c.approx_lng]}
                    icon={BLUE_ICON}
                  >
                    <Popup>
                      <div style={{ minWidth: 160 }}>
                        <p style={{ fontWeight: 600, marginBottom: 2 }}>{c.first_name}</p>
                        <p style={{ fontSize: 13, color: "#666" }}>
                          {t("map.bookings", { count: c.booking_count })}
                        </p>
                        <p style={{ fontSize: 11, color: "#999", marginTop: 4, fontStyle: "italic" }}>
                          {t("map.approxNote")}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MarkerClusterGroup>
            </>
          ) : null}
        </MapContainer>
      </div>

      {isProvider && customersQuery.isLoading ? (
        <p className="text-muted-foreground">{t("common.loading")}</p>
      ) : null}
      {isProvider && !customersQuery.isLoading && customers.length === 0 ? (
        <p className="text-muted-foreground">{t("map.noCustomers")}</p>
      ) : null}
      {!isProvider && providersQuery.isLoading ? (
        <p className="text-muted-foreground">{t("common.loading")}</p>
      ) : null}
    </div>
  );
}
