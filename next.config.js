/** @type {import('next').NextConfig} */
const nextConfig = {
  // We dont actually need this unless we are targeting a diff route
  // rewrites: async () => {
  //   return [
  //     {
  //       source: "/api/text/:path*",
  //       destination:
  //         process.env.NODE_ENV === "development"
  //           ? "http://127.0.0.1:8000/api/text/:path*"
  //           : "/api/text/:path*",
  //     },
  //   ];
  // },
};

module.exports = nextConfig;
