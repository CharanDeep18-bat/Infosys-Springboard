
import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { supabase } from "../lib/supabase";

// Create authentication context
const AuthContext = createContext(null);
function clearLegacyPrivateStorage() {
  const keys = [
    "finresearch_reports_v6",
    "finresearch_kb_records_v3",
    "finresearch_orchestration_state_v4"
  ];

  try {
    for (const key of keys) {
      localStorage.removeItem(key);
    }

    for (let i = localStorage.length - 1; i >= 0; i--) {
      const key = localStorage.key(i);

      if (key?.startsWith("finresearch_chat_history_v5_")) {
        localStorage.removeItem(key);
      }
    }
  } catch (error) {
    console.warn("Legacy cache cleanup failed");
  }
}
// Provider component
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    clearLegacyPrivateStorage();
    // Listen for authentication changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        setLoading(false);
      }
    );

    // Get the existing session
    supabase.auth.getSession().then(({ data, error }) => {
      if (error) {
        console.error("Session error:", error.message);
      }

      setSession(data?.session ?? null);
      setUser(data?.session?.user ?? null);
      setLoading(false);
    });

    // Cleanup listener when component unmounts
    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Google sign-in
  const signInWithGoogle = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: window.location.origin,
      },
    });

    return { error };
  };

  // Sign out
  const signOut = async () => {
    const { error } = await supabase.auth.signOut();

    if (!error) {
      clearLegacyPrivateStorage();
    }

    return { error };
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        loading,
        signInWithGoogle,
        signOut,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// Custom hook to access authentication
export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider"
    );
  }

  return context;
}
