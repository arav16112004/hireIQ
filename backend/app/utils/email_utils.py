"""
Email utilities for sending candidate communications
Uses SendGrid for reliable email delivery
"""
import os
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings
from app.core.logger import logger


def send_oa_email(
    to_email: str,
    candidate_name: str,
    oa_link: str,
    company_name: str = "SeroHire"
) -> bool:
    """
    Send the OA invitation email to a candidate
    
    Args:
        to_email: Candidate's email address
        candidate_name: Candidate's full name
        oa_link: Direct link to start the OA assessment
        company_name: Company name for branding
    
    Returns:
        True if email sent successfully, False otherwise
    """
    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=to_email,
        subject=f"Your Online Assessment – {company_name}",
        html_content=f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f4f4;padding:20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color:#ffffff;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding:40px 40px 20px;text-align:center;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border-radius:8px 8px 0 0;">
                            <h1 style="color:#ffffff;margin:0;font-size:28px;font-weight:bold;">{company_name}</h1>
                            <p style="color:#e0e7ff;margin:10px 0 0;font-size:14px;">AI-Driven Hiring Platform</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding:40px;">
                            <h2 style="color:#333333;margin:0 0 20px;font-size:24px;">Hi {candidate_name},</h2>
                            
                            <p style="color:#555555;line-height:1.6;margin:0 0 15px;font-size:16px;">
                                Congratulations! 🎉 You've been shortlisted for the next round of our hiring process.
                            </p>
                            
                            <p style="color:#555555;line-height:1.6;margin:0 0 15px;font-size:16px;">
                                We'd like to invite you to complete an online coding assessment. This will help us better understand your technical skills and problem-solving abilities.
                            </p>
                            
                            <div style="background-color:#f8f9fa;border-left:4px solid #667eea;padding:15px;margin:20px 0;">
                                <p style="color:#666666;margin:0;font-size:14px;line-height:1.5;">
                                    <strong>⏱️ Time Limit:</strong> 60 minutes<br>
                                    <strong>📝 Format:</strong> Coding challenges with automated grading<br>
                                    <strong>💻 Languages:</strong> Python, JavaScript, C++, Java, and more
                                </p>
                            </div>
                            
                            <p style="color:#555555;line-height:1.6;margin:20px 0 30px;font-size:16px;">
                                Click the button below to start your assessment:
                            </p>
                            
                            <!-- CTA Button -->
                            <div style="text-align:center;margin:30px 0;">
                                <a href="{oa_link}" 
                                   style="display:inline-block;background-color:#667eea;color:#ffffff;
                                          padding:16px 40px;text-decoration:none;border-radius:6px;
                                          font-size:16px;font-weight:bold;box-shadow:0 4px 6px rgba(102,126,234,0.3);">
                                    Start Assessment →
                                </a>
                            </div>
                            
                            <p style="color:#777777;line-height:1.6;margin:30px 0 0;font-size:14px;">
                                Or copy and paste this link into your browser:<br>
                                <a href="{oa_link}" style="color:#667eea;word-break:break-all;">{oa_link}</a>
                            </p>
                            
                            <hr style="border:none;border-top:1px solid #eeeeee;margin:30px 0;">
                            
                            <p style="color:#555555;line-height:1.6;margin:0 0 10px;font-size:16px;">
                                Best of luck! 🚀
                            </p>
                            <p style="color:#555555;line-height:1.6;margin:0;font-size:16px;">
                                <strong>The {company_name} Team</strong>
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding:20px 40px;background-color:#f8f9fa;border-radius:0 0 8px 8px;text-align:center;">
                            <p style="color:#999999;margin:0;font-size:12px;line-height:1.5;">
                                This is an automated message from {company_name}.<br>
                                Please do not reply to this email.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
    )

    try:
        if not settings.sendgrid_api_key:
            logger.warning(
                f"SendGrid API key not configured. Would send OA email to {to_email}"
            )
            logger.info(f"OA Link: {oa_link}")
            return False
        
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        
        logger.info(
            f"✅ OA email sent to {to_email} (status {response.status_code})"
        )
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send OA email to {to_email}: {str(e)}")
        return False


def send_interview_invitation(
    to_email: str,
    candidate_name: str,
    interview_link: str,
    interview_time: Optional[str] = None
) -> bool:
    """
    Send interview invitation email
    
    Args:
        to_email: Candidate's email
        candidate_name: Candidate's name
        interview_link: Link to join interview
        interview_time: Scheduled time (optional)
    
    Returns:
        True if sent successfully
    """
    time_info = f"<p><strong>Scheduled Time:</strong> {interview_time}</p>" if interview_time else ""
    
    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=to_email,
        subject="Interview Invitation – SeroHire",
        html_content=f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;line-height:1.6;padding:20px;">
    <h2>Hi {candidate_name},</h2>
    <p>Congratulations on passing the online assessment! We'd like to invite you for the next round.</p>
    {time_info}
    <p><a href="{interview_link}" 
          style="background-color:#667eea;color:white;padding:12px 24px;
                 text-decoration:none;border-radius:5px;display:inline-block;">
        Join Interview
    </a></p>
    <p>Best regards,<br>The SeroHire Team</p>
</body>
</html>
        """
    )
    
    try:
        if not settings.sendgrid_api_key:
            logger.warning(f"SendGrid not configured. Would send interview invite to {to_email}")
            return False
        
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        logger.info(f"✅ Interview invitation sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send interview invitation: {str(e)}")
        return False


def send_rejection_email(
    to_email: str,
    candidate_name: str,
    reason: Optional[str] = None
) -> bool:
    """
    Send rejection email (polite and encouraging)
    
    Args:
        to_email: Candidate's email
        candidate_name: Candidate's name
        reason: Optional feedback
    
    Returns:
        True if sent successfully
    """
    feedback = f"<p>{reason}</p>" if reason else ""
    
    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=to_email,
        subject="Update on Your Application – SeroHire",
        html_content=f"""
<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;line-height:1.6;padding:20px;">
    <h2>Hi {candidate_name},</h2>
    <p>Thank you for taking the time to apply and complete our assessment.</p>
    <p>After careful consideration, we've decided to move forward with other candidates 
       whose experience more closely matches our current needs.</p>
    {feedback}
    <p>We appreciate your interest in SeroHire and encourage you to apply for future opportunities 
       that match your skills and experience.</p>
    <p>Best wishes in your job search!</p>
    <p>Sincerely,<br>The SeroHire Team</p>
</body>
</html>
        """
    )
    
    try:
        if not settings.sendgrid_api_key:
            logger.warning(f"SendGrid not configured. Would send rejection to {to_email}")
            return False
        
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        logger.info(f"Rejection email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send rejection email: {str(e)}")
        return False

