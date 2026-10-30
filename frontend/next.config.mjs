/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async redirects() {
    return [
      {
        source: '/dashboard/progress',
        destination: '/dashboard/reports',
        permanent: false,
      },
    ]
  },
}

export default nextConfig
