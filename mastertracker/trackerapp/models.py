from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import timedelta

class Demand(models.Model):
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateField(null=True, blank=True)
    duration_months = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name
        
    def get_end_date(self):
        if self.start_date and self.duration_months:
            # Calculate end date based on start date and duration in months
            year = self.start_date.year + ((self.start_date.month - 1 + self.duration_months) // 12)
            month = ((self.start_date.month - 1 + self.duration_months) % 12) + 1
            # Try to use the same day, but handle month length differences
            try:
                return self.start_date.replace(year=year, month=month)
            except ValueError:
                # Handle case where the day doesn't exist in the target month (e.g., Feb 30)
                # Use the last day of the month instead
                if month == 12:
                    next_month = 1
                    next_year = year + 1
                else:
                    next_month = month + 1
                    next_year = year
                return self.start_date.replace(year=next_year, month=next_month, day=1) - timedelta(days=1)
        return None

class Stage(models.TextChoices):
    DEMAND_TO_BE_INITIATED = 'demand_to_be_initiated', _('Demand to be Initiated')
    DEMAND_INITIATED = 'demand_initiated', _('Demand Initiated')
    SPC_CLEARED = 'spc_cleared', _('SPC Cleared')
    DEMAND_APPROVED = 'demand_approved', _('Demand Approved')
    TENDER_ENQUIRY_FLOATED = 'tender_enquiry_floated', _('Tender Enquiry Floated')
    RECEIPT_OF_QUOTATIONS = 'receipt_of_quotations', _('Receipt of Quotations')
    TENDER_OPENING = 'tender_opening', _('Tender Opening')
    TCEC_APPROVED = 'tcec_approved', _('TCEC Approved')
    TPC_APPROVED = 'tpc_approved', _('TPC Approved')
    FINANCIAL_SANCTION = 'financial_sanction', _('Financial Sanction')
    ORDER_PLACEMENT = 'order_placement', _('Order Placement')
    PDR = 'pdr', _('PDR')
    SO_FOR_CRITICAL_BOM_BY_DEV_PARTNER = 'so_for_critical_bom_by_dev_partner', _('SO for Critical BoM by Dev Partner')
    DDR = 'ddr', _('DDR')
    CDR = 'cdr', _('CDR')
    ACCEPTANCE_OF_CRITICAL_BOM_BY_DEV_PARTNER = 'acceptance_of_critical_bom_by_dev_partner', _('Acceptance of Critical BoM by Dev Partner')
    REALIZATION_COMPLETED = 'realization_completed', _('Realization Completed')
    FAT_COMPLETED = 'fat_completed', _('FAT Completed')
    ATP_QTP_COMPLETED = 'atp_qtp_completed', _('ATP/QTP Completed')
    DELIVERY_AT_STORES = 'delivery_at_stores', _('Delivery at Stores')
    SAT_SOFT = 'sat_soft', _('SAT/SoFT')
    INWARD_INSPECTION_CLEARANCE = 'inward_inspection_clearance', _('Inward Inspection Clearance')
    PAYMENT_PROCESS = 'payment_process', _('Payment Process')
    PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
    PAYMENT_RELEASED = 'payment_released', _('Payment Released')
    AVAILABLE_FOR_INTEGRATION = 'available_for_integration', _('Available for Integration')

STAGE_COLORS = {
    Stage.DEMAND_TO_BE_INITIATED: "#1f78b4",
    Stage.DEMAND_INITIATED: "#33a02c",
    Stage.SPC_CLEARED: "#fb9a99",
    Stage.DEMAND_APPROVED: "#e31a1c",
    Stage.TENDER_ENQUIRY_FLOATED: "#fdbf6f",
    Stage.RECEIPT_OF_QUOTATIONS: "#ff7f00",
    Stage.TENDER_OPENING: "#cab2d6",
    Stage.TCEC_APPROVED: "#6a3d9a",
    Stage.TPC_APPROVED: "#b2df8a",
    Stage.FINANCIAL_SANCTION: "#a6cee3",
    Stage.ORDER_PLACEMENT: "#1f78b4",
    Stage.PDR: "#33a02c",
    Stage.SO_FOR_CRITICAL_BOM_BY_DEV_PARTNER: "#fb9a99",
    Stage.DDR: "#e31a1c",
    Stage.CDR: "#fdbf6f",
    Stage.ACCEPTANCE_OF_CRITICAL_BOM_BY_DEV_PARTNER: "#ff7f00",
    Stage.REALIZATION_COMPLETED: "#cab2d6",
    Stage.FAT_COMPLETED: "#6a3d9a",
    Stage.ATP_QTP_COMPLETED: "#b2df8a",
    Stage.DELIVERY_AT_STORES: "#a6cee3",
    Stage.SAT_SOFT: "#1f78b4",
    Stage.INWARD_INSPECTION_CLEARANCE: "#33a02c",
    Stage.PAYMENT_PROCESS: "#fb9a99",
    Stage.PARTIALLY_PAID: "#e31a1c",
    Stage.PAYMENT_RELEASED: "#fdbf6f",
    Stage.AVAILABLE_FOR_INTEGRATION: "#ff7f00",
    # Custom stage for mini progress bar
    'mini_progress': "#444444",  # Dark grey color for mini progress bar
}

STAGE_ORDER = {
    Stage.DEMAND_TO_BE_INITIATED: 0,
    Stage.DEMAND_INITIATED: 1,
    Stage.SPC_CLEARED: 2,
    Stage.DEMAND_APPROVED: 3,
    Stage.TENDER_ENQUIRY_FLOATED: 4,
    Stage.RECEIPT_OF_QUOTATIONS: 5,
    Stage.TENDER_OPENING: 6,
    Stage.TCEC_APPROVED: 7,
    Stage.TPC_APPROVED: 8,
    Stage.FINANCIAL_SANCTION: 9,
    Stage.ORDER_PLACEMENT: 10,
    Stage.PDR: 11,
    Stage.SO_FOR_CRITICAL_BOM_BY_DEV_PARTNER: 12,
    Stage.DDR: 13,
    Stage.CDR: 14,
    Stage.ACCEPTANCE_OF_CRITICAL_BOM_BY_DEV_PARTNER: 15,
    Stage.REALIZATION_COMPLETED: 16,
    Stage.FAT_COMPLETED: 17,
    Stage.ATP_QTP_COMPLETED: 18,
    Stage.DELIVERY_AT_STORES: 19,
    Stage.SAT_SOFT: 20,
    Stage.INWARD_INSPECTION_CLEARANCE: 21,
    Stage.PAYMENT_PROCESS: 22,
    Stage.PARTIALLY_PAID: 23,
    Stage.PAYMENT_RELEASED: 24,
    Stage.AVAILABLE_FOR_INTEGRATION: 25,
}

class DemandStagePeriod(models.Model):
    demand = models.ForeignKey(Demand, on_delete=models.CASCADE, related_name='stages')
    stage = models.CharField(max_length=50, choices=Stage.choices)
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = ('demand', 'stage')

    def duration_in_days(self):
        return (self.end_date - self.start_date).days + 1
