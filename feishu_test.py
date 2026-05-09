#!/usr/bin/env python3
"""
Manual script to test Feishu bot integration
"""

import logging
from datetime import datetime
from config import get_all_accounts, FEISHU_WEBHOOK_URL, FEISHU_ENABLED, get_account_feishu_webhook
from youtube_api import YouTubeAPI
from database import Database
from feishu_bot import FeishuBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_stats.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_feishu_connection():
    """Test Feishu bot connection"""
    logger.info("=" * 60)
    logger.info("Testing Feishu bot connection")
    logger.info("=" * 60)
    
    if not FEISHU_ENABLED:
        logger.error("❌ Feishu bot is not enabled in .env")
        return False
    
    if not FEISHU_WEBHOOK_URL:
        logger.error("❌ FEISHU_WEBHOOK_URL is not configured")
        return False
    
    try:
        logger.info(f"Testing webhook: {FEISHU_WEBHOOK_URL[:50]}...")
        result = FeishuBot.test_connection(FEISHU_WEBHOOK_URL)
        
        if result:
            logger.info("✓ Feishu bot connection test passed!")
        else:
            logger.error("❌ Feishu bot connection test failed!")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error testing Feishu connection: {e}")
        return False

def send_test_message():
    """Send test message to Feishu"""
    logger.info("=" * 60)
    logger.info("Sending test message to Feishu")
    logger.info("=" * 60)
    
    if not FEISHU_ENABLED:
        logger.error("❌ Feishu bot is not enabled")
        return False
    
    try:
        feishu = FeishuBot(FEISHU_WEBHOOK_URL)
        test_message = """
🎬 YouTube 数据统计机器人测试消息

这是一条测试消息，用于验证飞书机器人集成是否工作正常。

✅ 如果你看到了这条消息，说明配置成功！

📝 接下来的步骤：
1. 运行 python manual_run.py 来手动执行数据收集
2. 或运行 python main.py 来启动定时任务
3. 系统会在指定时间（默认08:00）自动推送数据到飞书

🔗 GitHub: https://github.com/python-goodfans/youtube-channel-stats
"""
        
        result = feishu.send_text_message(test_message)
        
        if result:
            logger.info("✓ Test message sent successfully!")
        else:
            logger.error("❌ Failed to send test message!")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error sending test message: {e}")
        return False

def send_sample_report():
    """Send sample report to Feishu"""
    logger.info("=" * 60)
    logger.info("Sending sample report to Feishu")
    logger.info("=" * 60)
    
    if not FEISHU_ENABLED:
        logger.error("❌ Feishu bot is not enabled")
        return False
    
    # Create sample data
    sample_channels_data = [
        {
            'channel_name': '示例频道 1',
            'current': {
                'subscribers': 50000,
                'video_count': 200,
                'view_count': 5000000
            },
            'previous': {
                'subscribers': 49500,
                'video_count': 199,
                'view_count': 4950000
            }
        },
        {
            'channel_name': '示例频道 2',
            'current': {
                'subscribers': 100000,
                'video_count': 350,
                'view_count': 15000000
            },
            'previous': {
                'subscribers': 99000,
                'video_count': 350,
                'view_count': 14800000
            }
        }
    ]
    
    try:
        feishu = FeishuBot(FEISHU_WEBHOOK_URL)
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = feishu.send_detailed_report('示例账号', sample_channels_data, today)
        
        if result:
            logger.info("✓ Sample report sent successfully!")
        else:
            logger.error("❌ Failed to send sample report!")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Error sending sample report: {e}")
        return False

def collect_and_send_real_data():
    """Collect real data and send to Feishu"""
    logger.info("=" * 60)
    logger.info("Collecting real data and sending to Feishu")
    logger.info("=" * 60)
    
    if not FEISHU_ENABLED:
        logger.error("❌ Feishu bot is not enabled")
        return False
    
    try:
        accounts = get_all_accounts()
        
        if not accounts:
            logger.error("❌ No accounts configured")
            return False
        
        logger.info(f"Processing {len(accounts)} account(s)")
        
        success_count = 0
        
        for account in accounts:
            account_id = account.get('account_id')
            account_name = account.get('account_name')
            channels = account.get('channels', [])
            api_key = account.get('api_key')
            
            logger.info(f"\nProcessing: {account_name}")
            
            try:
                # Initialize
                youtube_api = YouTubeAPI(api_key=api_key)
                db = Database()
                
                # Add account to database
                db.add_account(account_id, account_name)
                
                # Get today's date
                today = datetime.now().strftime('%Y-%m-%d')
                
                # Batch fetch all channels
                stats_dict = youtube_api.get_multiple_channel_stats(channels)
                
                if not stats_dict:
                    logger.warning(f"No stats for {account_name}")
                    continue
                
                # Process collected stats
                channels_data = []
                
                for channel_id in channels:
                    if channel_id not in stats_dict:
                        continue
                    
                    stats = stats_dict[channel_id]
                    
                    # Save to database
                    db.add_channel(account_id, channel_id, stats['channel_name'])
                    db.save_stats(
                        account_id,
                        channel_id,
                        today,
                        stats['subscribers'],
                        stats['video_count'],
                        stats['view_count']
                    )
                    
                    # Get previous stats
                    previous = db.get_previous_stats(account_id, channel_id, today)
                    
                    channels_data.append({
                        'channel_name': stats['channel_name'],
                        'current': {
                            'subscribers': stats['subscribers'],
                            'video_count': stats['video_count'],
                            'view_count': stats['view_count']
                        },
                        'previous': {
                            'subscribers': previous[0],
                            'video_count': previous[1],
                            'view_count': previous[2]
                        }
                    })
                    
                    logger.info(f"  ✓ {stats['channel_name']}: {stats['subscribers']:,} subscribers")
                
                if not channels_data:
                    logger.warning(f"No valid data for {account_name}")
                    continue
                
                # Send to Feishu
                webhook_url = get_account_feishu_webhook(account_id)
                feishu = FeishuBot(webhook_url)
                
                if feishu.send_detailed_report(account_name, channels_data, today):
                    logger.info(f"✓ Feishu message sent for {account_name}")
                    success_count += 1
                else:
                    logger.error(f"❌ Failed to send Feishu message for {account_name}")
            
            except Exception as e:
                logger.error(f"❌ Error processing {account_name}: {e}", exc_info=True)
        
        logger.info(f"\n✓ Successfully sent {success_count}/{len(accounts)} Feishu messages")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"❌ Error in collect_and_send_real_data: {e}", exc_info=True)
        return False

def main():
    """Main test function"""
    logger.info("\n" + "=" * 60)
    logger.info("YouTube Feishu Bot Integration Test")
    logger.info("=" * 60 + "\n")
    
    # Test 1: Connection
    logger.info("\n[Test 1/4] Testing Feishu connection...")
    if not test_feishu_connection():
        logger.error("Connection test failed. Please check your FEISHU_WEBHOOK_URL")
        return
    
    # Test 2: Send test message
    logger.info("\n[Test 2/4] Sending test message...")
    send_test_message()
    
    # Test 3: Send sample report
    logger.info("\n[Test 3/4] Sending sample report...")
    send_sample_report()
    
    # Test 4: Collect and send real data
    logger.info("\n[Test 4/4] Collecting and sending real data...")
    collect_and_send_real_data()
    
    logger.info("\n" + "=" * 60)
    logger.info("All tests completed!")
    logger.info("=" * 60 + "\n")

if __name__ == '__main__':
    main()
