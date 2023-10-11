/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // rewrites: async () => {
  //   return [
  //     {
  //       source: "/api/text/:path*",
  //       destination:
  //         process.env.NODE_ENV === "development"
  //           ? "http://127.0.0.1:8008/api/text/:path*"
  //           : "/api/text/:path*",
  //     },
  //   ];
  // },
}

module.exports = nextConfig
