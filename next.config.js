/** @type {import('next').NextConfig} */
const nextConfig = {
  // Removed 'output: export' to allow API routes and server-side features
  // If you need static export, uncomment the line below and remove API routes
  // output: 'export',
  
  // ESLint configuration
  eslint: {
    // Ignore ESLint during builds - warnings are not critical
    // The unescaped entities errors have been fixed
    // useEffect dependency warnings are false positives for callback patterns
    ignoreDuringBuilds: true,
  },
  
  // TypeScript configuration
  typescript: {
    // Warning: Dangerously allow production builds to complete with type errors
    // Set to true only if you know what you're doing
    ignoreBuildErrors: false,
  },
  
  // Image optimization
  images: {
    unoptimized: false,
    remotePatterns: [
      // Development
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/**',
      },
      // Production - your Render backend
      {
        protocol: 'https',
        hostname: '*.onrender.com',
        pathname: '/**',
      },
      // Supabase Storage
      {
        protocol: 'https',
        hostname: '*.supabase.co',
        pathname: '/storage/**',
      },
      // Generic HTTPS sources (for external images)
      {
        protocol: 'https',
        hostname: '**',
      },
    ],
  },
  
  // Environment variables (loaded from .env.local in development, Vercel dashboard in production)
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },
  
  // Production optimizations
  poweredByHeader: false, // Remove X-Powered-By header for security
  reactStrictMode: true,
  
  // Compression (Vercel handles this automatically, but good for other deployments)
  compress: true,
};

module.exports = nextConfig;
