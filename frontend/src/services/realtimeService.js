/**
 * realtimeService.js — Supabase Broadcast realtime subscriptions
 * Uses Supabase Broadcast channels (no Postgres table required).
 * Channel name format: occupancy-{parkingLotId}
 */

import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY;

let _supabase = null;

function getClient() {
  if (!_supabase) {
    if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
      console.warn(
        "[RealtimeService] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set. " +
        "Realtime updates disabled."
      );
      return null;
    }
    _supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
  }
  return _supabase;
}

/**
 * Subscribe to occupancy updates for a specific parking lot.
 *
 * @param {string} parkingLotId   - UUID of the parking lot
 * @param {function} onUpdate     - Callback called with occupancy payload
 * @returns {object|null}          - Supabase channel (pass to unsubscribe())
 */
export function subscribeToOccupancy(parkingLotId, onUpdate) {
  const client = getClient();
  if (!client) return null;

  const channelName = `occupancy-${parkingLotId}`;

  const channel = client.channel(channelName, {
    config: { broadcast: { self: false } },
  });

  channel
    .on("broadcast", { event: "occupancy_update" }, ({ payload }) => {
      if (typeof onUpdate === "function") {
        onUpdate(payload);
      }
    })
    .subscribe((status) => {
      if (status === "SUBSCRIBED") {
        console.debug(`[RealtimeService] Subscribed to ${channelName}`);
      }
    });

  return channel;
}

/**
 * Subscribe to global occupancy updates (all lots).
 * Used by AdminPanel for platform-wide monitoring.
 *
 * @param {function} onUpdate - Callback called with occupancy payload
 * @returns {object|null}
 */
export function subscribeToAllOccupancy(onUpdate) {
  const client = getClient();
  if (!client) return null;

  const channel = client.channel("occupancy-global");

  channel
    .on("broadcast", { event: "occupancy_update" }, ({ payload }) => {
      if (typeof onUpdate === "function") {
        onUpdate(payload);
      }
    })
    .subscribe();

  return channel;
}

/**
 * Remove a Supabase channel subscription.
 * Call this in useEffect cleanup.
 *
 * @param {object} channel - Channel returned by subscribe*()
 */
export function unsubscribe(channel) {
  if (!channel) return;
  try {
    const client = getClient();
    if (client) client.removeChannel(channel);
  } catch (e) {
    console.warn("[RealtimeService] Error removing channel:", e);
  }
}
