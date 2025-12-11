import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

// Create a singleton pattern to avoid multiple instances
let supabaseInstance: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient {
  if (supabaseInstance) {
    return supabaseInstance;
  }

  if (!supabaseUrl || !supabaseAnonKey) {
    // In development, provide a helpful error message
    if (process.env.NODE_ENV === 'development') {
      console.error(
        '[Supabase] Missing environment variables. Please check your .env.local file:\n' +
        '- NEXT_PUBLIC_SUPABASE_URL\n' +
        '- NEXT_PUBLIC_SUPABASE_ANON_KEY'
      );
    }
    throw new Error(
      'Missing Supabase configuration. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.'
    );
  }

  supabaseInstance = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  });

  return supabaseInstance;
}

// Export as a getter to enable lazy initialization
export const supabase = getSupabaseClient();



