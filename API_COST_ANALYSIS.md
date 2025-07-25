# AI API Cost Analysis for Suggesterr

## Overview

This document provides a comprehensive cost analysis comparing Google Gemini and OpenAI APIs for the Suggesterr application.

## API Pricing (as of July 2025)

### Google Gemini 2.0 Flash
- **Input tokens**: $0.075 per 1M tokens
- **Output tokens**: $0.30 per 1M tokens
- **Free tier**: 15 requests per minute, 1500 requests per day

### OpenAI GPT-4o-mini
- **Input tokens**: $0.15 per 1M tokens
- **Output tokens**: $0.60 per 1M tokens
- **No free tier** (usage-based billing from first request)

## Typical Usage Patterns in Suggesterr

### 1. Movie Recommendations Page Load
**Frequency**: Each time user visits recommendations page

**Gemini Request:**
- Input: ~800 tokens (prompt + user preferences + library context)
- Output: ~400 tokens (10 movie recommendations in JSON)
- **Cost per request**: $0.0001 (Gemini) vs $0.00036 (OpenAI)

**Daily usage for active user**: ~10 page loads
- **Gemini**: $0.001/day
- **OpenAI**: $0.0036/day

### 2. Chat Recommendations
**Frequency**: Interactive chat sessions

**Per message:**
- Input: ~1200 tokens (prompt + conversation history + context)
- Output: ~300 tokens (conversational response)
- **Cost per message**: $0.00018 (Gemini) vs $0.00036 (OpenAI)

**Daily usage for active user**: ~20 chat messages
- **Gemini**: $0.0036/day
- **OpenAI**: $0.0072/day

### 3. Mood and Similar Movie Recommendations
**Frequency**: When user explores different moods or similar movies

**Per request:**
- Input: ~600 tokens (simpler prompts)
- Output: ~350 tokens (8-6 recommendations)
- **Cost per request**: $0.00015 (Gemini) vs $0.00030 (OpenAI)

**Daily usage for active user**: ~5 requests
- **Gemini**: $0.00075/day
- **OpenAI**: $0.0015/day

## Cost Comparison Summary

### Per Active User Per Day
| Feature | Gemini Cost | OpenAI Cost | Difference |
|---------|-------------|-------------|------------|
| Page loads (10x) | $0.001 | $0.0036 | 3.6x more expensive |
| Chat messages (20x) | $0.0036 | $0.0072 | 2x more expensive |
| Mood requests (5x) | $0.00075 | $0.0015 | 2x more expensive |
| **Total daily** | **$0.00535** | **$0.01230** | **2.3x more expensive** |

### Monthly Costs (30 days)
- **Gemini**: $0.16 per active user
- **OpenAI**: $0.37 per active user

### Projected Costs for Different User Bases

| Users | Gemini Monthly | OpenAI Monthly | Annual Difference |
|-------|----------------|----------------|-------------------|
| 100 | $16 | $37 | $252 |
| 500 | $80 | $185 | $1,260 |
| 1,000 | $160 | $370 | $2,520 |
| 2,500 | $400 | $925 | $6,300 |

## Key Considerations

### Gemini Advantages
1. **Cost Effective**: ~57% cheaper than OpenAI
2. **Free Tier**: 1,500 requests/day free (good for development/testing)
3. **Rate Limits**: More generous for hobby projects

### OpenAI Advantages
1. **Quality**: Potentially higher quality responses
2. **Reliability**: More stable API with better uptime
3. **Features**: Advanced reasoning capabilities

## Recommendations

### For Small Deployments (< 500 users)
- **Use Gemini** as primary provider
- **Estimated monthly cost**: $80-400
- Set up OpenAI as fallback for premium features

### For Medium Deployments (500-2000 users)
- **Start with Gemini** ($400-1,600/month)
- **Monitor quality metrics** closely
- Consider OpenAI for specific high-value interactions

### For Large Deployments (> 2000 users)
- **Hybrid approach**: Gemini for bulk recommendations, OpenAI for chat
- **Estimated savings**: 40-60% vs pure OpenAI
- Implement intelligent routing based on request complexity

## Cost Optimization Strategies

1. **Smart Caching**: Cache recommendations for 1-2 hours to reduce API calls
2. **Request Batching**: Group similar requests when possible
3. **Context Trimming**: Limit conversation history to last 10 messages
4. **Fallback Logic**: Use free tier limits efficiently before switching to paid

## Implementation Notes

The toggle switch allows users to choose their preferred AI provider in settings. This enables:
- **A/B testing** of response quality
- **Cost management** by defaulting to Gemini
- **Premium features** with OpenAI for paying subscribers
- **Graceful degradation** if one service is down

## Updated CLAUDE.md Instructions

Remember to add these environment variables:
```env
# Required for Gemini (existing)
GOOGLE_GEMINI_API_KEY=your-gemini-api-key

# Required for OpenAI support
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
```