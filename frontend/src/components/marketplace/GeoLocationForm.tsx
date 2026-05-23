import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { GeoLocationWrite } from "@/lib/marketplace-api";

type GeoLocationFormProps = {
  value: GeoLocationWrite;
  onChange: (next: GeoLocationWrite) => void;
  idPrefix?: string;
};

export function GeoLocationForm({ value, onChange, idPrefix = "geo" }: GeoLocationFormProps) {
  function set(field: keyof GeoLocationWrite, fieldValue: string) {
    onChange({ ...value, [field]: fieldValue });
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor={`${idPrefix}-line1`}>Address line 1</Label>
        <Input
          id={`${idPrefix}-line1`}
          required
          value={value.address_line1 ?? ""}
          onChange={(e) => set("address_line1", e.target.value)}
          className="min-h-14 text-lg rounded-2xl"
        />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-city`}>City</Label>
          <Input
            id={`${idPrefix}-city`}
            required
            value={value.city ?? ""}
            onChange={(e) => set("city", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-postal`}>Postal code</Label>
          <Input
            id={`${idPrefix}-postal`}
            value={value.postal_code ?? ""}
            onChange={(e) => set("postal_code", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-region`}>Region</Label>
          <Input
            id={`${idPrefix}-region`}
            value={value.region ?? ""}
            onChange={(e) => set("region", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-country`}>Country</Label>
          <Input
            id={`${idPrefix}-country`}
            required
            value={value.country ?? "RO"}
            onChange={(e) => set("country", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-lat`}>Latitude (optional)</Label>
          <Input
            id={`${idPrefix}-lat`}
            type="number"
            step="any"
            value={value.latitude ?? ""}
            onChange={(e) => set("latitude", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor={`${idPrefix}-lng`}>Longitude (optional)</Label>
          <Input
            id={`${idPrefix}-lng`}
            type="number"
            step="any"
            value={value.longitude ?? ""}
            onChange={(e) => set("longitude", e.target.value)}
            className="min-h-14 text-lg rounded-2xl"
          />
        </div>
      </div>
    </div>
  );
}
