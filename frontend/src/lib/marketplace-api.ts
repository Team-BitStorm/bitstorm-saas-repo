import { apiFetch } from "./api";

export type GeoLocation = {
  id?: number;
  label?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  region?: string;
  postal_code?: string;
  country?: string;
  latitude?: string | number | null;
  longitude?: string | number | null;
};

export type GeoLocationWrite = Omit<GeoLocation, "id">;

export type Service = {
  id: number;
  slug: string;
  name: string;
  description: string;
  price_min: string;
  price_max: string;
  is_active: boolean;
};

export type Language = {
  id: number;
  code: string;
  name: string;
};

export type CustomerProfile = {
  id: number;
  avatar_url: string;
  bio: string;
  home_location: GeoLocation | null;
};

export type ProviderProfile = {
  id: number;
  display_name: string;
  bio: string;
  service_area: GeoLocation | null;
  travel_radius_km: number | null;
  is_active: boolean;
};

export type ServiceOffering = {
  id: number;
  service: Service;
  provider_price: string;
  duration_minutes: number | null;
  created_at: string;
  updated_at: string;
};

export type AvailabilityRule = {
  id: number;
  weekday: number;
  start_time: string;
  end_time: string;
  timezone: string;
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
};

export type AvailabilitySlot = {
  id: number;
  rule: number | null;
  service: Service | null;
  starts_at: string;
  ends_at: string;
  status: "open" | "booked" | "blocked" | "cancelled";
};

/**
 * Provider service-area location — a public business centroid.
 * Coordinates are intentionally included; this is NOT a customer domicile.
 * Customer home addresses are protected separately (owner_user checks, §11.1).
 */
export type PublicGeoLocation = {
  id?: number;
  city?: string;
  region?: string;
  country?: string;
  latitude?: string | number | null;
  longitude?: string | number | null;
};

export type MarketplaceProvider = {
  id: number;
  display_name: string;
  bio: string;
  service_area: PublicGeoLocation | null;
  travel_radius_km: number | null;
  is_active: boolean;
  languages: Language[];
  offerings: ServiceOffering[];
  distance_km: string | null;
};

/** Approximate customer location returned to provider callers (§11.2) */
export type ApproxCustomerLocation = {
  customer_id: number;
  approx_lat: number;
  approx_lng: number;
  radius_m: number;
};

export type ApproxCustomerListItem = {
  customer_id: number;
  first_name: string;
  approx_lat: number;
  approx_lng: number;
  radius_m: number;
  booking_count: number;
};

export type MarketplaceSlot = {
  id: number;
  service: Service | null;
  starts_at: string;
  ends_at: string;
  status: string;
};

export type Booking = {
  id: number;
  provider?: number;
  provider_name?: string;
  customer?: number;
  customer_email?: string;
  customer_name?: string;
  service: Service;
  starts_at: string;
  ends_at: string;
  price: string;
  price_min: string;
  price_max: string;
  travel_km: string | null;
  travel_time_minutes: number | null;
  duration_minutes: number | null;
  status: string;
  notes: string;
  visit_location: GeoLocation | null;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
};

export async function fetchServices(): Promise<Service[]> {
  return apiFetch<Service[]>("/api/core/services/");
}

export async function fetchLanguages(): Promise<Language[]> {
  return apiFetch<Language[]>("/api/core/languages/");
}

export async function fetchCustomerProfile(): Promise<CustomerProfile> {
  return apiFetch<CustomerProfile>("/api/me/customer-profile/");
}

export async function updateCustomerProfile(data: {
  avatar_url?: string;
  bio?: string;
}): Promise<CustomerProfile> {
  return apiFetch<CustomerProfile>("/api/me/customer-profile/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchHomeLocation(): Promise<GeoLocation | null> {
  try {
    return await apiFetch<GeoLocation>("/api/me/home-location/");
  } catch (err) {
    if (err instanceof Error && "status" in err && (err as { status: number }).status === 404) {
      return null;
    }
    throw err;
  }
}

export async function saveHomeLocation(data: GeoLocationWrite): Promise<GeoLocation> {
  return apiFetch<GeoLocation>("/api/me/home-location/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchProviderProfile(): Promise<ProviderProfile> {
  return apiFetch<ProviderProfile>("/api/me/provider-profile/");
}

export async function updateProviderProfile(data: {
  display_name?: string;
  bio?: string;
  travel_radius_km?: number;
  is_active?: boolean;
}): Promise<ProviderProfile> {
  return apiFetch<ProviderProfile>("/api/me/provider-profile/", {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function fetchServiceArea(): Promise<GeoLocation | null> {
  try {
    return await apiFetch<GeoLocation>("/api/me/service-area/");
  } catch (err) {
    if (err instanceof Error && "status" in err && (err as { status: number }).status === 404) {
      return null;
    }
    throw err;
  }
}

export async function saveServiceArea(data: GeoLocationWrite): Promise<GeoLocation> {
  return apiFetch<GeoLocation>("/api/me/service-area/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function fetchOfferings(): Promise<ServiceOffering[]> {
  return apiFetch<ServiceOffering[]>("/api/provider/offerings/");
}

export async function createOffering(data: {
  service_id: number;
  provider_price: string;
  duration_minutes?: number;
}): Promise<ServiceOffering> {
  return apiFetch<ServiceOffering>("/api/provider/offerings/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteOffering(id: number): Promise<void> {
  await apiFetch(`/api/provider/offerings/${id}/`, { method: "DELETE" });
}

export async function fetchAvailabilityRules(): Promise<AvailabilityRule[]> {
  return apiFetch<AvailabilityRule[]>("/api/provider/availability/rules/");
}

export async function createAvailabilityRule(
  data: Omit<AvailabilityRule, "id">,
): Promise<AvailabilityRule> {
  return apiFetch<AvailabilityRule>("/api/provider/availability/rules/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteAvailabilityRule(id: number): Promise<void> {
  await apiFetch(`/api/provider/availability/rules/${id}/`, { method: "DELETE" });
}

export async function generateSlots(weeks = 4): Promise<AvailabilitySlot[]> {
  return apiFetch<AvailabilitySlot[]>("/api/provider/availability/generate/", {
    method: "POST",
    body: JSON.stringify({ weeks }),
  });
}

export async function fetchMyAvailabilitySlots(params?: {
  status?: string;
  from?: string;
  to?: string;
}): Promise<AvailabilitySlot[]> {
  const search = new URLSearchParams();
  if (params?.status) search.set("status", params.status);
  if (params?.from) search.set("from", params.from);
  if (params?.to) search.set("to", params.to);
  const qs = search.toString();
  return apiFetch<AvailabilitySlot[]>(
    `/api/provider/availability/slots/${qs ? `?${qs}` : ""}`,
  );
}

export async function createProviderSlot(data: {
  service_id?: number;
  starts_at: string;
  ends_at: string;
}): Promise<AvailabilitySlot> {
  return apiFetch<AvailabilitySlot>("/api/provider/availability/slots/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function setSlotStatus(
  id: number,
  status: "open" | "blocked" | "cancelled",
): Promise<AvailabilitySlot> {
  return apiFetch<AvailabilitySlot>(`/api/provider/availability/slots/${id}/status/`, {
    method: "POST",
    body: JSON.stringify({ status }),
  });
}

export async function fetchProviderBookings(): Promise<Booking[]> {
  return apiFetch<Booking[]>("/api/provider/bookings/");
}

export async function providerBookingAction(
  id: number,
  action: "confirm" | "decline" | "complete",
): Promise<Booking> {
  return apiFetch<Booking>(`/api/provider/bookings/${id}/${action}/`, { method: "POST" });
}

export async function providerReviewBooking(
  id: number,
  rating: number,
  comment: string,
): Promise<unknown> {
  return apiFetch(`/api/provider/bookings/${id}/review/`, {
    method: "POST",
    body: JSON.stringify({ rating, comment }),
  });
}

export async function discoverProviders(params?: {
  service?: string;
  language?: string;
  lat?: string;
  lng?: string;
}): Promise<MarketplaceProvider[]> {
  const search = new URLSearchParams();
  if (params?.service) search.set("service", params.service);
  if (params?.language) search.set("language", params.language);
  if (params?.lat) search.set("lat", params.lat);
  if (params?.lng) search.set("lng", params.lng);
  const qs = search.toString();
  const data = await apiFetch<MarketplaceProvider[] | { results: MarketplaceProvider[] }>(
    `/api/marketplace/providers/${qs ? `?${qs}` : ""}`,
    { skipAuth: true },
  );
  return Array.isArray(data) ? data : data.results;
}

export async function fetchProviderDetail(
  id: number,
  params?: { lat?: string; lng?: string },
): Promise<MarketplaceProvider> {
  const search = new URLSearchParams();
  if (params?.lat) search.set("lat", params.lat);
  if (params?.lng) search.set("lng", params.lng);
  const qs = search.toString();
  return apiFetch<MarketplaceProvider>(
    `/api/marketplace/providers/${id}/${qs ? `?${qs}` : ""}`,
    { skipAuth: true },
  );
}

export async function fetchMarketplaceProviderSlots(
  providerId: number,
  params?: { from?: string; to?: string; service?: string },
): Promise<MarketplaceSlot[]> {
  const search = new URLSearchParams();
  if (params?.from) search.set("from", params.from);
  if (params?.to) search.set("to", params.to);
  if (params?.service) search.set("service", params.service);
  const qs = search.toString();
  return apiFetch<MarketplaceSlot[]>(
    `/api/marketplace/providers/${providerId}/slots/${qs ? `?${qs}` : ""}`,
    { skipAuth: true },
  );
}

export async function fetchCustomerBookings(): Promise<Booking[]> {
  return apiFetch<Booking[]>("/api/customer/bookings/");
}

export async function createBooking(data: {
  provider_id: number;
  service_id: number;
  provider_availability_id: number;
  notes?: string;
}): Promise<Booking> {
  return apiFetch<Booking>("/api/customer/bookings/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function cancelBooking(id: number): Promise<Booking> {
  return apiFetch<Booking>(`/api/customer/bookings/${id}/cancel/`, { method: "POST" });
}

export async function customerReviewBooking(
  id: number,
  rating: number,
  comment: string,
): Promise<unknown> {
  return apiFetch(`/api/customer/bookings/${id}/review/`, {
    method: "POST",
    body: JSON.stringify({ rating, comment }),
  });
}

export async function fetchCustomerApproxLocation(
  customerId: number,
): Promise<ApproxCustomerLocation> {
  return apiFetch<ApproxCustomerLocation>(
    `/api/provider/customers/${customerId}/location/`,
  );
}

export async function fetchAllCustomerApproxLocations(): Promise<ApproxCustomerListItem[]> {
  return apiFetch<ApproxCustomerListItem[]>("/api/provider/customers/");
}

export function isProfileComplete(
  role: "customer" | "provider",
  profile: CustomerProfile | ProviderProfile | null,
  location: GeoLocation | null,
): boolean {
  if (!profile) return false;
  if (role === "customer") {
    const cp = profile as CustomerProfile;
    return Boolean(cp.bio?.trim() || cp.avatar_url) && Boolean(location?.address_line1);
  }
  const pp = profile as ProviderProfile;
  return Boolean(pp.display_name?.trim()) && Boolean(location?.city) && pp.travel_radius_km != null;
}
