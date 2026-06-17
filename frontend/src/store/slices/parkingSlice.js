import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { parkingAPI } from "../../services/api";
import toast from "react-hot-toast";

// ── Thunks ────────────────────────────────────────────────────────────────────
export const searchParking = createAsyncThunk(
  "parking/search",
  async (params, { rejectWithValue }) => {
    try {
      const { data } = await parkingAPI.search(params);
      return data;
    } catch (err) {
      toast.error("Search failed. Please try again.");
      return rejectWithValue(err.response?.data);
    }
  }
);

export const fetchOwnerLots = createAsyncThunk("parking/fetchOwnerLots", async (_, { rejectWithValue }) => {
  try {
    const { data } = await parkingAPI.getLots();
    return data.results || data;
  } catch (err) {
    return rejectWithValue(err.response?.data);
  }
});

export const fetchLotOccupancy = createAsyncThunk(
  "parking/fetchOccupancy",
  async (lotId, { rejectWithValue }) => {
    try {
      const { data } = await parkingAPI.getOccupancy(lotId);
      return { lotId, slots: data };
    } catch (err) {
      return rejectWithValue(err.response?.data);
    }
  }
);

// ── Slice ─────────────────────────────────────────────────────────────────────
const parkingSlice = createSlice({
  name: "parking",
  initialState: {
    searchResults: [],
    searchParams: {},
    ownerLots: [],
    selectedLot: null,
    occupancy: {},        // { [lotId]: [slots] }
    loading: false,
    searchLoading: false,
    error: null,
  },
  reducers: {
    setSelectedLot(state, action) {
      state.selectedLot = action.payload;
    },
    setSearchParams(state, action) {
      state.searchParams = action.payload;
    },
    clearSearch(state) {
      state.searchResults = [];
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(searchParking.pending, (state) => { state.searchLoading = true; })
      .addCase(searchParking.fulfilled, (state, action) => {
        state.searchLoading = false;
        state.searchResults = action.payload;
      })
      .addCase(searchParking.rejected, (state) => { state.searchLoading = false; })

      .addCase(fetchOwnerLots.pending, (state) => { state.loading = true; })
      .addCase(fetchOwnerLots.fulfilled, (state, action) => {
        state.loading = false;
        state.ownerLots = action.payload;
      })
      .addCase(fetchOwnerLots.rejected, (state) => { state.loading = false; })

      .addCase(fetchLotOccupancy.fulfilled, (state, action) => {
        state.occupancy[action.payload.lotId] = action.payload.slots;
      });
  },
});

export const { setSelectedLot, setSearchParams, clearSearch } = parkingSlice.actions;
export default parkingSlice.reducer;
