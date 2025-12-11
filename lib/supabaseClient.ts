import { createClient, SupabaseClient } from '@supabase/supabase-js';

// Create a singleton pattern to avoid multiple instances
let supabaseInstance: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient {
  if (supabaseInstance) {
    return supabaseInstance;
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    // During build time, return a mock client that will be replaced at runtime
    if (typeof window === 'undefined') {
      // Server-side during build - create a placeholder that won't be used
      return createClient('https://placeholder.supabase.co', 'placeholder-key', {
        auth: {
          autoRefreshToken: false,
          persistSession: false,
        },
      });
    }
    // Client-side without env vars - this is an error
    console.error(
      '[Supabase] Missing environment variables. Please check your .env.local file:\n' +
      '- NEXT_PUBLIC_SUPABASE_URL\n' +
      '- NEXT_PUBLIC_SUPABASE_ANON_KEY'
    );
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
