/** @type {import('next').NextConfig} */
const nextConfig = {
  // Removed 'output: export' to allow API routes and server-side features
  // If you need static export, uncomment the line below and remove API routes
  // output: 'export',
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    unoptimized: false, // Enable image optimization for better performance
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/**',
      },
      {
        protocol: 'https',
        hostname: '**', // Allow images from any HTTPS source (for production)
      },
    ],
    domains: ['localhost'], // Add your image domains here if needed (deprecated, using remotePatterns instead)
  },
  env: {
    // Environment variables are loaded from .env.local
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || '',
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || '',
  },
};

module.exports = nextConfig;
