'use client'

/**
 * Browse Apps menu
 */
const AppsBrowser = () => {
  const appLink = 'https://brain-dump-dieharders.vercel.app/'

  return (
    <div className="z-5 mb-32 grid text-center lg:mb-0 lg:grid-cols-4 lg:text-left">
      <a
        href={appLink}
        className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        target="_blank"
        rel="noopener noreferrer"
      >
        <h2 className="mb-3 text-xl font-semibold">
          Learn{' '}
          <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
            -&gt;
          </span>
        </h2>
        <p className="m-0 max-w-[30ch] text-sm opacity-50">
          Find in-depth information and share it. Search and analyze private data with agents.
        </p>
      </a>

      <a
        href={appLink}
        className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        target="_blank"
        rel="noopener noreferrer"
      >
        <h2 className="mb-3 text-xl font-semibold">
          Create{' '}
          <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
            -&gt;
          </span>
        </h2>
        <p className="m-0 max-w-[30ch] text-sm opacity-50">
          Find inspiration, kick-off a project or just toss ideas around with a creative avatar.
        </p>
      </a>

      <a
        href={appLink}
        className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        target="_blank"
        rel="noopener noreferrer"
      >
        <h2 className="mb-3 text-xl font-semibold">
          Heal{' '}
          <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
            -&gt;
          </span>
        </h2>
        <p className="m-0 max-w-[30ch] text-sm opacity-50">
          Explore your mind then reflect on your journey with an ai buddy by your side.
        </p>
      </a>

      <a
        href={appLink}
        className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        target="_blank"
        rel="noopener noreferrer"
      >
        <h2 className="mb-3 text-xl font-semibold">
          Grow{' '}
          <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
            -&gt;
          </span>
        </h2>
        <p className="m-0 max-w-[30ch] text-sm opacity-50">
          Plan, adapt, enact. Take advantage of critical thinking processes to reach your goals.
        </p>
      </a>
    </div>
  )
}

export default AppsBrowser
