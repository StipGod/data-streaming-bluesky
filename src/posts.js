const axios = require('axios');

const validateAtUri = (uri) => {
  const atUriPattern = /^at:\/\/did:plc:[a-z0-9]+\/app\.bsky\.feed\.post\/[a-z0-9]+$/;
  return atUriPattern.test(uri);
};

const fetchPosts = async (uris) => {
  try {
    console.log('AT-URIs:', uris);

    // Validate and encode AT-URIs
    const validatedUris = uris.filter((uri) => validateAtUri(uri));
    if (validatedUris.length === 0) {
      throw new Error('No valid AT-URIs provided.');
    }
    const encodedUris = validatedUris.map(encodeURIComponent);

    // Log the request URL
    console.log(
      'Request URL:',
      `https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris=${encodedUris.join(',')}`
    );

    // Make the API request
    const response = await axios.get(
      'https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts',
      {
        params: {
          uris: encodedUris.join(','),
        },
      }
    );
    console.log('Post Details:', response.data.posts);
  } catch (error) {
    console.error(
      'Error fetching post details:',
      error.response?.data || error.message
    );
  }
};

// Your AT-URIs
const atUris = [
  'at://did:plc:jv6e7b2f2h4cbkjahjihnmwo/app.bsky.feed.post/3lbdgwvbcg42x',
  'at://did:plc:oky5czdrnfjpqslsw2a5iclo/app.bsky.feed.post/3lbd2eaura22r',
  'at://did:plc:z72i7hdynmk6r22z27h6tvur/app.bsky.feed.post/3lb6vz4ms6c25',
];

fetchPosts(atUris);