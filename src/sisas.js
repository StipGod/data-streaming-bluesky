const { BskyAgent } = require('@atproto/api');
require('dotenv').config();

const agent = new BskyAgent({
  service: 'https://bsky.social',
});

const identifier = process.env.IDENTIFIER;
const password = process.env.PASSWORD;

(async () => {
  try {
    await agent.login({
      identifier,
      password,
    });

    const timelineResponse = await agent.getTimeline();
    const feed = timelineResponse.data.feed;

    console.log('Timeline Response Feed:', feed);

    // Correctly extract AT-URIs from nested post objects
    const atUris = feed.map((item) => item?.post?.uri || 'URI not found');
    console.log('Your AT-URIs:', atUris);
  } catch (error) {
    console.error('Error fetching AT-URIs:', error.message);
  }
})();

