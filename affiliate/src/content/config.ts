import { defineCollection, z } from 'astro:content';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    category: z.enum(['mature', 'bbw', 'regional', 'general']),
    tags: z.array(z.string()).default([]),
    heroEmoji: z.string().default('💬'),
    featuredOffer: z.string().optional(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
