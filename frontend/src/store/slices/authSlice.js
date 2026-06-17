import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import { authAPI } from "../../services/api";
import toast from "react-hot-toast";

// ── Thunks ────────────────────────────────────────────────────────────────────
export const loginUser = createAsyncThunk("auth/login", async (credentials, { rejectWithValue }) => {
  try {
    const { data } = await authAPI.login(credentials);
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    toast.success(`Welcome back, ${data.user.full_name}!`);
    return data;
  } catch (err) {
    toast.error(err.response?.data?.detail || "Login failed");
    return rejectWithValue(err.response?.data);
  }
});

export const registerUser = createAsyncThunk("auth/register", async (payload, { rejectWithValue }) => {
  try {
    const { data } = await authAPI.register(payload);
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    toast.success("Account created successfully!");
    return data;
  } catch (err) {
    const message =
      err.response?.data?.detail ||
      err.response?.data?.email?.[0] ||
      err.response?.data?.non_field_errors?.[0] ||
      "Registration failed. Please verify the form and try again.";
    toast.error(message);
    return rejectWithValue(err.response?.data || { detail: message });
  }
});

export const fetchProfile = createAsyncThunk("auth/fetchProfile", async (_, { rejectWithValue }) => {
  try {
    const { data } = await authAPI.profile();
    return data;
  } catch (err) {
    return rejectWithValue(err.response?.data);
  }
});

// ── Slice ─────────────────────────────────────────────────────────────────────
const authSlice = createSlice({
  name: "auth",
  initialState: {
    user: null,
    isAuthenticated: !!localStorage.getItem("access_token"),
    loading: false,
    error: null,
  },
  reducers: {
    logout(state) {
      state.user = null;
      state.isAuthenticated = false;
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      toast.success("Logged out successfully");
    },
    clearError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    const pending  = (state) => { state.loading = true;  state.error = null; };
    const rejected = (state, action) => { state.loading = false; state.error = action.payload; };

    builder
      .addCase(loginUser.pending, pending)
      .addCase(loginUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(loginUser.rejected, rejected)

      .addCase(registerUser.pending, pending)
      .addCase(registerUser.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.isAuthenticated = true;
      })
      .addCase(registerUser.rejected, rejected)

      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.user = action.payload;
      });
  },
});

export const { logout, clearError } = authSlice.actions;
export default authSlice.reducer;
